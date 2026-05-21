from django.db import models
from django.contrib.auth.models import User


# -----------------------------
# Doctor Model
# -----------------------------
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"Dr. {self.user.username}"


# -----------------------------
# Patient Model
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

    contact_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


# -----------------------------
# Pill Schedule
# -----------------------------
class PillSchedule(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='schedules'
    )

    pill_name = models.CharField(max_length=100)

    dosage = models.CharField(max_length=50)

    time = models.TimeField()

    frequency = models.CharField(
        max_length=50,
        default='Daily'
    )

    start_date = models.DateField()

    end_date = models.DateField()

    def __str__(self):
        return f"{self.pill_name} for {self.patient.name}"


# -----------------------------
# Pill Intake Tracking
# -----------------------------
class PillIntake(models.Model):

    schedule = models.ForeignKey(
        PillSchedule,
        on_delete=models.CASCADE,
        related_name='intakes'
    )

    date = models.DateField()

    taken = models.BooleanField(default=False)

    taken_time = models.TimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.schedule.pill_name} - {self.date}"


# -----------------------------
# Pill Box Status
# -----------------------------
class PillBoxStatus(models.Model):

    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name='pillbox_status'
    )

    slot_status = models.JSONField(default=dict)
    # Example:
    # {"slot1":"filled","slot2":"empty"}

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pill Box for {self.patient.name}"


# -----------------------------
# Alerts
# -----------------------------
class Alert(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='alerts'
    )

    message = models.TextField()

    alert_type = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.alert_type} - {self.patient.name}"


# -----------------------------
# Refill Logs
# -----------------------------
class RefillLog(models.Model):

    pill_name = models.CharField(max_length=100)

    count = models.IntegerField()

    timestamp = models.DateTimeField(auto_now_add=True)

    refill_needed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.pill_name} - {self.count}"


# -----------------------------
# Medication Schedule
# -----------------------------
class Medication(models.Model):

    FREQUENCY_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
    ]

    STATUS_CHOICES = [
        ('Assigned', 'Assigned'),
        ('Taken', 'Taken'),
        ('Missed', 'Missed'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medications'
    )

    name = models.CharField(max_length=100)

    dosage = models.CharField(max_length=50)

    # IMPORTANT FIX
    # Changed from CharField -> TimeField
    time = models.TimeField()

    # Motor / Slot number
    compartment = models.IntegerField()

    frequency = models.CharField(
        max_length=50,
        choices=FREQUENCY_CHOICES,
        default='Daily'
    )

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Assigned'
    )

    last_taken = models.DateTimeField(
        null=True,
        blank=True
    )

    # Prevent duplicate dispensing
    last_dispensed_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.patient.name})"


# -----------------------------
# Dispense Logs
# -----------------------------
class Dispense(models.Model):

    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='dispense_logs'
    )

    pill_name = models.CharField(max_length=100)

    compartment = models.IntegerField()

    time_dispensed = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        default='Dispensed'
    )

    def __str__(self):
        return f"{self.pill_name} - Compartment {self.compartment}"