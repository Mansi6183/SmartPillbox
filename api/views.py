from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from datetime import date
import json
import uuid
import paho.mqtt.client as mqtt

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action, api_view

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

from .utils import auto_generate_all_alerts


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
            return Response({"error": "Invalid credentials"}, status=401)

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
# DISPENSE API (MQTT)
# =========================================================
class DispenseViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get', 'post'], url_path='trigger')
    def trigger(self, request):
        try:
            data = request.GET if request.method == "GET" else request.data

            hour = int(data.get("hour", 0))
            minute = int(data.get("minute", 0))
            motor = int(data.get("motor", 1))
            dose = int(data.get("dose", 1))

            if not (0 <= hour <= 23):
                return Response({"error": "Invalid hour"}, status=400)

            if not (0 <= minute <= 59):
                return Response({"error": "Invalid minute"}, status=400)

            if motor not in [1, 2, 3]:
                return Response({"error": "Invalid motor"}, status=400)

            payload = json.dumps({
                "hour": hour,
                "minute": minute,
                "motor": motor,
                "dose": dose
            })

            client = mqtt.Client()
            client.connect("broker.hivemq.com", 1883, 60)
            client.publish("pillbox/schedule", payload)
            client.disconnect()

            return Response({
                "message": "Sent successfully",
                "payload": json.loads(payload)
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)


# =========================================================
# SAVE SCHEDULE (FIXED)
# =========================================================
@api_view(['POST'])
def save_schedule(request):
    try:
        data = request.data

        hour = data.get("hour")
        minute = data.get("minute")
        motor = data.get("motor")
        patient_id = data.get("patient")

        if not all([hour, minute, motor, patient_id]):
            return Response({"error": "Missing fields"}, status=400)

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=404)

        time_value = f"{int(hour):02d}:{int(minute):02d}:00"

        medication = Medication.objects.create(
            patient=patient,
            name=f"Motor {motor} Medicine",
            dosage="1 Tablet",
            time=time_value,
            compartment=int(motor),
            frequency="Daily",
            start_date=date.today()
        )

        return Response({
            "message": "Saved successfully",
            "id": medication.id,
            "time": time_value
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


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

            client = mqtt.Client()
            client.connect("broker.hivemq.com", 1883, 60)
            client.publish("pillbox/schedule", json.dumps(payload))
            client.disconnect()

            return Response({
                "message": "Sent successfully",
                "payload": payload
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)


# =========================================================
# DOCTOR
# =========================================================
class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


# =========================================================
# PATIENT (FIXED)
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
# PILL SCHEDULE (MQTT AUTO)
# =========================================================
class PillScheduleViewSet(viewsets.ModelViewSet):
    queryset = PillSchedule.objects.all()
    serializer_class = PillScheduleSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        schedule = serializer.save()

        try:
            hour, minute, _ = map(int, str(schedule.time).split(":"))

            payload = {
                "hour": hour,
                "minute": minute,
                "motor": 1,
                "dose": 1
            }

            client = mqtt.Client()
            client.connect("broker.hivemq.com", 1883, 60)
            client.publish("pillbox/schedule", json.dumps(payload))
            client.disconnect()

        except Exception as e:
            print("MQTT Error:", str(e))


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

    def perform_create(self, serializer):
        serializer.save()   # CLEAN FIX (no patient_id bugs)


# =========================================================
# DELETE PATIENT
# =========================================================
class PatientDeleteView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def delete(self, request, pk):
        try:
            patient = Patient.objects.get(pk=pk)
            user = patient.user
            patient.delete()
            user.delete()

            return Response({"message": "Deleted"}, status=204)

        except Patient.DoesNotExist:
            return Response({"error": "Not found"}, status=404)


# =========================================================
# SIMPLE APIs
# =========================================================
class PillIntakeAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"message": "Recorded"})


class RefillStatusAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "OK"})


class RefillLogAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logs = RefillLog.objects.all()
        return Response(RefillLogSerializer(logs, many=True).data)


class VoiceAgentAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"message": "Voice working"})
