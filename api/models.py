from django.db import models
from django.contrib.auth.models import User


# -----------------------------
# Doctor model (linked to User)
# -----------------------------
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"Dr. {self.user.username}"


# -----------------------------
# Patient model (linked to User + Doctor)
# -----------------------------
class Patient(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)
    age = models.IntegerField()
    email = models.EmailField(
    unique=True,
    null=True,
    blank=True
)

    contact_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


    
    
    

# -----------------------------
# Pill Schedule
# -----------------------------
class PillSchedule(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='schedules')
    pill_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    time = models.TimeField()  # time of day to take pill
    frequency = models.CharField(max_length=50, default='Daily')  # e.g., Daily / Weekly
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.pill_name} for {self.patient.name}"


# -----------------------------
# Pill Intake
# -----------------------------
class PillIntake(models.Model):
    schedule = models.ForeignKey(PillSchedule, on_delete=models.CASCADE, related_name='intakes')
    date = models.DateField()
    taken = models.BooleanField(default=False)
    taken_time = models.TimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.schedule.pill_name} - {self.date}"


# -----------------------------
# Pill Box Status
# -----------------------------
class PillBoxStatus(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='pillbox_status')
    slot_status = models.JSONField(default=dict)  
    # Example: {"slot1": "filled", "slot2": "empty"}
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pill Box for {self.patient.name}"


# -----------------------------
# Alert
# -----------------------------
class Alert(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='alerts')
    message = models.TextField()
    alert_type = models.CharField(max_length=50)  # e.g., "Missed Dose", "Refill Reminder"
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.alert_type} - {self.patient.name}"

class RefillLog(models.Model):
    pill_name = models.CharField(max_length=100)
    count = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    refill_needed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.pill_name} - {self.count}"
    
class Medication(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    time = models.CharField(max_length=10)
    compartment = models.IntegerField()
    frequency = models.CharField(max_length=50)
    start_date = models.DateField()
    status = models.CharField(max_length=20, default='Assigned')
    last_taken = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.patient.name})"

