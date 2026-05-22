from rest_framework import serializers
from .models import (
    Patient,
    Doctor,
    PillSchedule,
    PillIntake,
    PillBoxStatus,
    Alert,
    RefillLog,
    Medication
)

# ----------------------------
# 👨‍⚕️ Doctor Serializer
# ----------------------------
class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = "__all__"


# ----------------------------
# 🔐 Login Serializer
# ----------------------------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


# ----------------------------
# 🧍 Patient Serializer (FIXED)
# ----------------------------
class PatientSerializer(serializers.ModelSerializer):
    # IMPORTANT: email must NOT be required (backend generates it)
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    # Frontend → Backend mappings
    fullName = serializers.CharField(
        source="name",
        required=False,
        allow_blank=True
    )

    phone = serializers.CharField(
        source="contact_number",
        required=False,
        allow_blank=True,
        allow_null=True
    )

    # Alternate email keys (frontend flexibility)
    userEmail = serializers.EmailField(
        source="email",
        required=False,
        allow_null=True
    )

    mail = serializers.EmailField(
        source="email",
        required=False,
        allow_null=True
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "name",
            "fullName",
            "age",
            "email",
            "userEmail",
            "mail",
            "phone",
            "address",
        ]

    def validate(self, data):
        # Only name is mandatory
        if not data.get("name"):
            raise serializers.ValidationError({
                "fullName": "Name is required"
            })
        return data

    # Email uniqueness check ONLY if email is provided
    def validate_email(self, value):
        if value and Patient.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Patient with this email already exists."
            )
        return value


# ----------------------------
# 💊 Pill Schedule
# ----------------------------
class PillScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillSchedule
        fields = "__all__"


# ----------------------------
# 💊 Pill Intake
# ----------------------------
class PillIntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillIntake
        fields = "__all__"


# ----------------------------
# 📦 Pill Box Status
# ----------------------------
class PillBoxStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillBoxStatus
        fields = "__all__"


# ----------------------------
# 🚨 Alert
# ----------------------------
class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = "__all__"


# ----------------------------
# 🔁 Refill Log
# ----------------------------
class RefillLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefillLog
        fields = "__all__"

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'