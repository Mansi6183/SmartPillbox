from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from datetime import date, datetime, timedelta
from django.utils import timezone
from .models import Doctor, Patient, PillSchedule, PillIntake, PillBoxStatus, Alert
from .serializers import (
    DoctorSerializer,
    LoginSerializer,
    PatientSerializer,
    PillScheduleSerializer,
    PillIntakeSerializer,
    PillBoxStatusSerializer,
    AlertSerializer
)

# ----------------------------
# 🔐 LOGIN VIEW
# ----------------------------
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)

            if user is not None:
                # Identify user role
                role = None
                if Doctor.objects.filter(user=user).exists():
                    role = "Doctor"
                elif Patient.objects.filter(user=user).exists():
                    role = "Patient"
                else:
                    role = "Unknown"

                return Response({
                    "message": "Login successful",
                    "role": role,
                    "username": user.username
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ----------------------------
# 🧩 CRUD VIEWSETS
# ----------------------------
class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer


class PillScheduleViewSet(viewsets.ModelViewSet):
    queryset = PillSchedule.objects.all()
    serializer_class = PillScheduleSerializer


class PillIntakeViewSet(viewsets.ModelViewSet):
    queryset = PillIntake.objects.all()
    serializer_class = PillIntakeSerializer


class PillBoxStatusViewSet(viewsets.ModelViewSet):
    queryset = PillBoxStatus.objects.all()
    serializer_class = PillBoxStatusSerializer


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer



# ----------------------------
# 💊 Custom Pill Intake Endpoint (IoT or Device Integration)
# ----------------------------
from datetime import datetime
from django.utils import timezone

class PillIntakeAPI(APIView):
    """
    Custom endpoint for IoT device to send pill intake data.
    Example JSON:
    {
        "patient_id": 1,
        "pill_name": "Paracetamol",
        "status": "Taken"
    }
    """
    def post(self, request):
        data = request.data
        patient_id = data.get("patient_id")
        pill_name = data.get("pill_name")
        status = data.get("status")  # "Taken" or "Missed"

        try:
            # Find schedule for that pill
            schedule = PillSchedule.objects.get(patient_id=patient_id, pill_name=pill_name)
            
            # Create or update pill intake record
            intake, created = PillIntake.objects.get_or_create(
                schedule=schedule,
                date=timezone.now().date(),
                defaults={
                    "taken": (status == "Taken"),
                    "taken_time": timezone.now().time() if status == "Taken" else None
                }
            )

            # If already exists, update it
            if not created:
                intake.taken = (status == "Taken")
                intake.taken_time = timezone.now().time() if status == "Taken" else None
                intake.save()

            # If missed → Create alert
            if status == "Missed":
                Alert.objects.create(
                    patient_id=patient_id,
                    message=f"{pill_name} was missed today!",
                    alert_type="Missed Dose"
                )

            return Response({"message": "Pill intake recorded successfully"}, status=200)

        except PillSchedule.DoesNotExist:
            return Response({"error": "Pill schedule not found"}, status=404)

# ----------------------------
# 💊 Refill Detection API
# ----------------------------
class RefillStatusAPI(APIView):
    """
    Check pill boxes and return patients who need refills.
    Works with PillBoxStatus model having JSONField slot_status.
    Example:
    slot_status = {
        "slot1": "filled",
        "slot2": "empty",
        "slot3": "filled"
    }
    """
    def get(self, request):
        refill_needed = []  # to store patients needing refill

        # Loop through all pill boxes
        for box in PillBoxStatus.objects.all():
            empty_slots = [slot for slot, status in box.slot_status.items() if status == "empty"]

            if empty_slots:
                refill_needed.append({
                    "patient": box.patient.name,
                    "empty_slots": empty_slots,
                    "last_updated": box.last_updated,
                })

        # Return result
        if refill_needed:
            return Response({
                "status": "Refill needed",
                "details": refill_needed
            })
        else:
            return Response({"status": "All slots filled"})
        
        # ----------------------------
# 🗣️ Voice Agent API (AI Voice Assistant Integration)
# ----------------------------
class VoiceAgentAPI(APIView):
    """
    Webhook endpoint for Dialogflow voice agent.
    Handles voice intents like:
    - "Remind me"
    - "Did I take pill?"
    - "Refill status"
    - "Missed pill status"
    """

    def post(self, request):
        # Extract intent name
        intent = request.data.get('queryResult', {}).get('intent', {}).get('displayName', '')
        response_text = "Sorry, I didn’t get that."

        # 1️⃣ Remind me
        if intent == "Remind me":
            response_text = "Okay, I’ll remind you to take your pill at the scheduled time."

        # 2️⃣ Did I take pill?
        elif intent == "Did I take pill?":
            last_intake = PillIntake.objects.filter(taken=True).order_by('-taken_time').first()
            if last_intake:
                time_str = last_intake.taken_time.strftime("%I:%M %p")
                response_text = f"You took your pill at {time_str} today."
            else:
                response_text = "You haven’t taken your pill yet today."

        # 3️⃣ Refill status
        elif intent == "Refill status":
            latest_box = PillBoxStatus.objects.order_by('-last_updated').first()
            if latest_box:
                empty_slots = [slot for slot, status in latest_box.slot_status.items() if status == "empty"]
                if empty_slots:
                    response_text = f"You need to refill {len(empty_slots)} slots: {', '.join(empty_slots)}."
                else:
                    response_text = "All your pill box slots are filled."
            else:
                response_text = "I couldn’t find your pill box data."

        # 4️⃣ Missed pill status
        elif intent == "Missed pill status":
            missed = PillIntake.objects.filter(taken=False, date=timezone.now().date())
            if missed.exists():
                response_text = "You missed your pill today. Please take it soon!"
            else:
                response_text = "Good job! You didn’t miss any pill today."

        # Log request for debugging
        print("Dialogflow Intent:", intent)

        # Respond to Dialogflow
        return Response({
            "fulfillmentText": response_text
        })
