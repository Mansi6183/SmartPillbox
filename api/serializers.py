from rest_framework import serializers
from .models import Patient, PillSchedule, PillIntake, PillBoxStatus, Alert
from .models import Doctor
from .models import RefillLog

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class PillScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillSchedule
        fields = '__all__'

class PillIntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillIntake
        fields = '__all__'

class PillBoxStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillBoxStatus
        fields = '__all__'

class AlertSerializer(serializers.ModelSerializer):  # ✅ Fixed name here
    class Meta:
        model = Alert  # ✅ Fixed model reference
        fields = '__all__'


class RefillLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefillLog
        fields = '__all__'
