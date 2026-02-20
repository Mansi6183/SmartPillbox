from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import uuid
import paho.mqtt.client as mqtt

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

# ----------------------------
# 🔐 LOGIN VIEW
# ----------------------------
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


# ----------------------------
# 💊 DISPENSE API (GET + POST)
# ----------------------------
class DispenseViewSet(viewsets.ViewSet):
    """
    ViewSet for medicine dispensing via MQTT.
    Appears in API Root and supports:
      GET  /api/dispense/
      POST /api/dispense/trigger/
      GET  /api/dispense/trigger/?motor=1&dose=2
    """

    # ✅ This ensures /api/dispense/ appears in API Root
    def list(self, request):
        return Response({
            "message": "Dispense API available",
            "usage": {
                "GET": "/api/dispense/trigger/?motor=1&dose=2",
                "POST": "/api/dispense/trigger/"
            }
        })

    # ✅ Trigger endpoint
    @action(detail=False, methods=['get', 'post'], url_path='trigger')
    def trigger(self, request):
        try:
            if request.method == "POST":
                hour = int(request.data.get("hour", 0))
                minute = int(request.data.get("minute", 0))
                motor = int(request.data.get("motor", 1))
                dose = int(request.data.get("dose", 1))
            else:
                motor = int(request.GET.get("motor", 1))
                dose = int(request.GET.get("dose", 1))
                hour, minute = 0, 0

            mqtt_message = json.dumps({
                "hour": hour,
                "minute": minute,
                "motor": motor,
                "dose": dose
            })

            mqtt_topic = "pillbox/schedule"
            broker = "broker.hivemq.com"

            client = mqtt.Client()
            client.connect(broker, 1883, 60)
            client.publish(mqtt_topic, mqtt_message)
            client.disconnect()

            print(f"📡 MQTT → {mqtt_topic}: {mqtt_message}")

            return Response({
                "status": "Motor activated via MQTT",
                "motor": motor,
                "dose": dose,
                "time": f"{hour:02d}:{minute:02d}",
                "mqtt_message": mqtt_message,
                "topic": mqtt_topic
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# ----------------------------
# 🧩 REFILL LOG API
# ----------------------------
class RefillLogAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logs = RefillLog.objects.all()
        serializer = RefillLogSerializer(logs, many=True)
        return Response(serializer.data)

    def post(self, request):
        pill_name = request.data.get("pill_name")
        count = int(request.data.get("count", 0))
        patient_id = request.data.get("patient_id")

        refill_needed = (count == 0)

        log = RefillLog.objects.create(
            pill_name=pill_name,
            count=count,
            refill_needed=refill_needed
        )

        if refill_needed and patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
                Alert.objects.create(
                    patient=patient,
                    message=f"Refill needed for {pill_name}",
                    alert_type="Refill Reminder"
                )
            except Patient.DoesNotExist:
                pass

        return Response(
            RefillLogSerializer(log).data,
            status=status.HTTP_201_CREATED
        )


# ----------------------------
# 📡 MQTT SCHEDULE API
# ----------------------------
# ----------------------------
# 📡 MQTT SCHEDULE API (Updated for ESP32 JSON)
# ----------------------------
class MQTTScheduleAPI(APIView):
    """
    POST /api/schedule/
    Body → {"time": "08:14:18", "motor": 1, "dose": 2}
    Publishes JSON → {"hour":8,"minute":14,"motor":1,"dose":2}
    Topic → pillbox/schedule
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Get values from request
            time_str = request.data.get("time")
            motor = int(request.data.get("motor", 0))
            dose = int(request.data.get("dose", 0))

            # Validate inputs
            if not time_str or motor not in [0, 1, 2] or dose <= 0:
                return Response(
                    {"error": "Invalid input. Example: {'time':'08:14:18','motor':1,'dose':2}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse hour and minute from time string
            try:
                hour, minute, _ = map(int, time_str.split(":"))
            except ValueError:
                return Response({"error": "Time format must be HH:MM:SS"}, status=400)

            # Prepare MQTT JSON payload
            payload = {
                "hour": hour,
                "minute": minute,
                "motor": motor,
                "dose": dose
            }

            broker = "broker.hivemq.com"
            topic = "pillbox/schedule"

            # Publish via MQTT
            client = mqtt.Client("RenderScheduler")
            client.connect(broker, 1883, 60)
            client.publish(topic, json.dumps(payload))
            client.disconnect()

            print(f"✅ MQTT → {topic}: {payload}")

            return Response({
                "message": "Schedule sent successfully",
                "topic": topic,
                "payload": payload
            }, status=200)

        except Exception as e:
            print("❌ MQTT Schedule Error:", str(e))
            return Response({"error": str(e)}, status=500)

# ----------------------------
# 👨‍⚕️ DOCTOR VIEWSET
# ----------------------------
class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


# ----------------------------
# 🧍 PATIENT VIEWSET
# ----------------------------
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


# ----------------------------
# 💊 CRUD VIEWSETS
# ----------------------------
# ----------------------------
# 💊 PILL SCHEDULE VIEWSET (Auto MQTT Publish)
# ----------------------------
class PillScheduleViewSet(viewsets.ModelViewSet):
    queryset = PillSchedule.objects.all()
    serializer_class = PillScheduleSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # 1️⃣ Save the new schedule to database
        schedule = serializer.save()

        # 2️⃣ Extract time, dosage, and (optional) motor info
        time_str = str(schedule.time)
        dosage = int(schedule.dosage) if schedule.dosage else 1
        motor = 1  # Default motor slot; you can map based on pill name if needed

        # 3️⃣ Parse "HH:MM:SS" → hour/minute
        try:
            hour, minute, _ = map(int, time_str.split(":"))
        except ValueError:
            print("⚠️ Invalid time format in schedule:", time_str)
            return

        # 4️⃣ Prepare MQTT JSON payload (for ESP32)
        payload = {
            "hour": hour,
            "minute": minute,
            "motor": motor,
            "dose": dosage
        }

        # 5️⃣ Publish via MQTT (to match ESP32 topic)
        try:
            broker = "broker.hivemq.com"
            topic = "pillbox/schedule"

            client = mqtt.Client("RenderAutoScheduler")
            client.connect(broker, 1883, 60)
            client.publish(topic, json.dumps(payload))
            client.disconnect()

            print(f"✅ Auto-MQTT Sent → {topic}: {payload}")

        except Exception as e:
            print("❌ MQTT Auto Publish Error:", str(e))


class PillIntakeViewSet(viewsets.ModelViewSet):
    queryset = PillIntake.objects.all()
    serializer_class = PillIntakeSerializer

class PillBoxStatusViewSet(viewsets.ModelViewSet):
    queryset = PillBoxStatus.objects.all()
    serializer_class = PillBoxStatusSerializer

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer

class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        patient_id = self.request.data.get('patientId')
        if patient_id:
            serializer.save(patient_id=patient_id)
        else:
            serializer.save()


# ----------------------------
# 🧍 PATIENT DELETE API
# ----------------------------
class PatientDeleteView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def delete(self, request, pk):
        try:
            patient = Patient.objects.select_related("user").get(pk=pk)
            user = patient.user
            patient.delete()
            user.delete()
            return Response({"message": "Patient deleted successfully"}, status=204)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=404)


# ----------------------------
# 💊 PILL INTAKE API (IoT)
# ----------------------------
class PillIntakeAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        patient_id = request.data.get("patient_id")
        pill_name = request.data.get("pill_name")
        status_value = request.data.get("status")

        try:
            schedule = PillSchedule.objects.get(patient_id=patient_id, pill_name=pill_name)
            intake, created = PillIntake.objects.get_or_create(
                schedule=schedule,
                date=timezone.now().date(),
                defaults={
                    "taken": status_value == "Taken",
                    "taken_time": timezone.now().time() if status_value == "Taken" else None
                }
            )
            if not created:
                intake.taken = (status_value == "Taken")
                intake.taken_time = timezone.now().time() if status_value == "Taken" else None
                intake.save()

            if status_value == "Missed":
                Alert.objects.create(
                    patient_id=patient_id,
                    message=f"{pill_name} was missed today!",
                    alert_type="Missed Dose"
                )

            return Response({"message": "Pill intake recorded successfully"}, status=200)
        except PillSchedule.DoesNotExist:
            return Response({"error": "Pill schedule not found"}, status=404)


# ----------------------------
# 💊 REFILL STATUS API
# ----------------------------
class RefillStatusAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        refill_needed = []
        for box in PillBoxStatus.objects.all():
            empty_slots = [slot for slot, status in box.slot_status.items() if status == "empty"]
            if empty_slots:
                refill_needed.append({"patient": box.patient.name, "empty_slots": empty_slots, "last_updated": box.last_updated})

        if refill_needed:
            return Response({"status": "Refill needed", "details": refill_needed})
        return Response({"status": "All slots filled"})


# ----------------------------
# 🗣️ VOICE AGENT API
# ----------------------------
class VoiceAgentAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        intent = request.data.get("queryResult", {}).get("intent", {}).get("displayName", "")
        response_text = "Sorry, I didn’t get that."

        if intent == "Remind me":
            response_text = "Okay, I’ll remind you to take your pill."
        elif intent == "Did I take pill?":
            last = PillIntake.objects.filter(taken=True).order_by("-taken_time").first()
            response_text = f"You took your pill at {last.taken_time.strftime('%I:%M %p')}." if last else "You haven’t taken your pill yet today."
        elif intent == "Refill status":
            box = PillBoxStatus.objects.order_by("-last_updated").first()
            if box:
                empty = [s for s, v in box.slot_status.items() if v == "empty"]
                response_text = f"You need to refill: {', '.join(empty)}" if empty else "All pill box slots are filled."
        elif intent == "Missed pill status":
            missed = PillIntake.objects.filter(taken=False, date=timezone.now().date())
            response_text = "You missed your pill today." if missed.exists() else "Great! You didn’t miss any pill today."

        return Response({"fulfillmentText": response_text})
