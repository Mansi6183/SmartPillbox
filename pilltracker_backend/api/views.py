from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action, api_view

import json
import uuid
from datetime import date

import paho.mqtt.client as mqtt

from .utils import auto_generate_all_alerts

from .models import (
    Doctor,
    Patient,
    PillSchedule,
    PillIntake,
    PillBoxStatus,
    Alert,
    RefillLog,
    Medication
)

from .serializers import (
    DoctorSerializer,
    RefillLogSerializer,
    LoginSerializer,
    PatientSerializer,
    PillScheduleSerializer,
    PillIntakeSerializer,
    PillBoxStatusSerializer,
    AlertSerializer,
    MedicationSerializer
)


# =========================================================
# LOGIN API
# =========================================================
class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )

        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        role = "Unknown"

        if Doctor.objects.filter(user=user).exists():
            role = "Doctor"

        elif Patient.objects.filter(user=user).exists():
            role = "Patient"

        return Response({
            "message": "Login successful",
            "role": role,
            "username": user.username
        })


# =========================================================
# DISPENSE API
# =========================================================
class DispenseViewSet(viewsets.ViewSet):

    permission_classes = [AllowAny]

    def list(self, request):

        return Response({
            "message": "Dispense API available",
            "usage": {
                "GET": "/api/dispense/trigger/?hour=14&minute=30&motor=1&dose=1",
                "POST": "/api/dispense/trigger/"
            }
        })

    @action(detail=False, methods=['get', 'post'], url_path='trigger')
    def trigger(self, request):

        try:

            # -------------------------
            # GET REQUEST
            # -------------------------
            if request.method == "GET":

                hour = int(request.GET.get("hour", 0))
                minute = int(request.GET.get("minute", 0))
                motor = int(request.GET.get("motor", 1))
                dose = int(request.GET.get("dose", 1))

            # -------------------------
            # POST REQUEST
            # -------------------------
            else:

                hour = int(request.data.get("hour", 0))
                minute = int(request.data.get("minute", 0))
                motor = int(request.data.get("motor", 1))
                dose = int(request.data.get("dose", 1))

            # -------------------------
            # VALIDATION
            # -------------------------
            if hour < 0 or hour > 23:
                return Response(
                    {"error": "Hour must be between 0 and 23"},
                    status=400
                )

            if minute < 0 or minute > 59:
                return Response(
                    {"error": "Minute must be between 0 and 59"},
                    status=400
                )

            if motor not in [1, 2, 3]:
                return Response(
                    {"error": "Motor must be 1, 2, or 3"},
                    status=400
                )

            # -------------------------
            # MQTT PAYLOAD
            # -------------------------
            payload = {
                "hour": hour,
                "minute": minute,
                "motor": motor,
                "dose": dose
            }

            mqtt_message = json.dumps(payload)

            broker = "broker.hivemq.com"
            topic = "pillbox/schedule"

            # -------------------------
            # MQTT SEND
            # -------------------------
            client = mqtt.Client()

            client.connect(broker, 1883, 60)

            client.publish(topic, mqtt_message)

            client.disconnect()

            print(f"✅ MQTT SENT → {mqtt_message}")

            return Response({

                "status": "Schedule sent successfully",

                "scheduled_time": f"{hour:02d}:{minute:02d}",

                "motor": motor,

                "dose": dose,

                "mqtt_topic": topic,

                "mqtt_message": payload
            })

        except Exception as e:

            print("❌ MQTT ERROR:", str(e))

            return Response({
                "error": str(e)
            }, status=500)


# =========================================================
# SAVE SCHEDULE API
# =========================================================
@api_view(['POST'])
def save_schedule(request):

    try:

        data = request.data

        hour = data.get("hour")
        minute = data.get("minute")
        motor = data.get("motor")

        if hour is None or minute is None or motor is None:

            return Response({
                "error": "hour, minute and motor required"
            }, status=400)

        time_value = f"{int(hour):02d}:{int(minute):02d}:00"

        # Get first patient
        patient = Patient.objects.first()

        if not patient:

            return Response({
                "error": "No patient found"
            }, status=400)

        # Save medication
        medication = Medication.objects.create(

            patient=patient,

            name=f"Motor {motor} Medicine",

            dosage="1 Tablet",

            time=time_value,

            compartment=int(motor),

            frequency="Daily",

            start_date=date.today()
        )

        print(f"✅ Saved schedule at {time_value}")

        return Response({

            "message": "Schedule saved successfully",

            "id": medication.id,

            "time": time_value,

            "motor": motor
        })

    except Exception as e:

        print("❌ SAVE ERROR:", str(e))

        return Response({
            "error": str(e)
        }, status=500)


# =========================================================
# MQTT SCHEDULE API
# =========================================================
class MQTTScheduleAPI(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        try:

            time_str = request.data.get("time")
            motor = int(request.data.get("motor", 1))
            dose = int(request.data.get("dose", 1))

            hour, minute, _ = map(int, time_str.split(":"))

            payload = {

                "hour": hour,

                "minute": minute,

                "motor": motor,

                "dose": dose
            }

            broker = "broker.hivemq.com"
            topic = "pillbox/schedule"

            client = mqtt.Client()

            client.connect(broker, 1883, 60)

            client.publish(topic, json.dumps(payload))

            client.disconnect()

            print(f"✅ MQTT SENT → {payload}")

            return Response({

                "message": "Schedule sent successfully",

                "payload": payload
            })

        except Exception as e:

            print("❌ MQTT Schedule Error:", str(e))

            return Response({
                "error": str(e)
            }, status=500)


# =========================================================
# DOCTOR VIEWSET
# =========================================================
class DoctorViewSet(viewsets.ModelViewSet):

    queryset = Doctor.objects.all()

    serializer_class = DoctorSerializer


# =========================================================
# PATIENT VIEWSET
# =========================================================
class PatientViewSet(viewsets.ModelViewSet):

    queryset = Patient.objects.all()

    serializer_class = PatientSerializer

    permission_classes = [AllowAny]

    @transaction.atomic
    def perform_create(self, serializer):

        user = User.objects.create_user(

            username=f"patient_{uuid.uuid4().hex[:8]}",

            password="patient123"
        )

        doctor = Doctor.objects.first()

        serializer.save(user=user, doctor=doctor)


# =========================================================
# PILL SCHEDULE VIEWSET
# =========================================================
class PillScheduleViewSet(viewsets.ModelViewSet):

    queryset = PillSchedule.objects.all()

    serializer_class = PillScheduleSerializer

    permission_classes = [AllowAny]

    def perform_create(self, serializer):

        schedule = serializer.save()

        time_str = str(schedule.time)

        dosage = 1

        try:

            hour, minute, _ = map(int, time_str.split(":"))

            payload = {

                "hour": hour,

                "minute": minute,

                "motor": 1,

                "dose": dosage
            }

            client = mqtt.Client()

            client.connect("broker.hivemq.com", 1883, 60)

            client.publish(
                "pillbox/schedule",
                json.dumps(payload)
            )

            client.disconnect()

            print(f"✅ Auto MQTT → {payload}")

        except Exception as e:

            print("❌ Auto MQTT Error:", str(e))


# =========================================================
# OTHER VIEWSETS
# =========================================================
class PillIntakeViewSet(viewsets.ModelViewSet):

    queryset = PillIntake.objects.all()

    serializer_class = PillIntakeSerializer


class PillBoxStatusViewSet(viewsets.ModelViewSet):

    queryset = PillBoxStatus.objects.all()

    serializer_class = PillBoxStatusSerializer


class AlertViewSet(viewsets.ModelViewSet):

    queryset = Alert.objects.all().order_by('-created_at')

    serializer_class = AlertSerializer

    def list(self, request, *args, **kwargs):

        auto_generate_all_alerts()

        return super().list(request, *args, **kwargs)

class MedicationViewSet(viewsets.ModelViewSet):

    queryset = Medication.objects.all()

    serializer_class = MedicationSerializer

    permission_classes = [AllowAny]

    # =========================================
    # RETURN ONLY LATEST SCHEDULE
    # =========================================
   def get_queryset(self):

    from django.utils import timezone

    now = timezone.localtime().time()

    patient_id = self.request.GET.get("patient")

    # Get medicines whose time is >= current time
    queryset = Medication.objects.filter(
        time__gte=now
    ).order_by('time')

    # Optional patient filter
    if patient_id:
        queryset = queryset.filter(patient_id=patient_id)

    # If all today's medicines are over,
    # start again from earliest medicine
    if not queryset.exists():

        queryset = Medication.objects.all().order_by('time')

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

    # Return ONLY next/current medicine
    return queryset[:1]

    # =========================================
    # SAVE + MQTT
    # =========================================
    def perform_create(self, serializer):

        obj = serializer.save()

        try:

            # FRONTEND TIME FORMAT = 17:00:00
            time_str = str(obj.time)

            hour, minute, _ = map(
                int,
                time_str.split(":")
            )

            payload = {

                "hour": hour,

                "minute": minute,

                "motor": int(obj.compartment),

                "dose": int(obj.dosage)
                if str(obj.dosage).isdigit()
                else 1
            }

            client = mqtt.Client()

            client.connect(
                "broker.hivemq.com",
                1883,
                60
            )

            client.publish(
                "pillbox/schedule",
                json.dumps(payload)
            )

            client.disconnect()

            print("🔥 MQTT SENT:", payload)

        except Exception as e:

            print("❌ MQTT ERROR:", str(e))
# =========================================================
# PATIENT DELETE API
# =========================================================
class PatientDeleteView(APIView):

    permission_classes = [AllowAny]

    @transaction.atomic
    def delete(self, request, pk):

        try:

            patient = Patient.objects.select_related("user").get(pk=pk)

            user = patient.user

            patient.delete()

            user.delete()

            return Response({
                "message": "Patient deleted successfully"
            }, status=204)

        except Patient.DoesNotExist:

            return Response({
                "error": "Patient not found"
            }, status=404)


# =========================================================
# PILL INTAKE API
# =========================================================
class PillIntakeAPI(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        return Response({
            "message": "Pill intake recorded successfully"
        })


# =========================================================
# REFILL STATUS API
# =========================================================
class RefillStatusAPI(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        return Response({
            "status": "All slots filled"
        })


# =========================================================
# REFILL LOG API
# =========================================================
class RefillLogAPI(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        logs = RefillLog.objects.all()

        serializer = RefillLogSerializer(logs, many=True)

        return Response(serializer.data)


# =========================================================
# VOICE AGENT API
# =========================================================
class VoiceAgentAPI(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        return Response({
            "fulfillmentText": "Voice API working"
        })


