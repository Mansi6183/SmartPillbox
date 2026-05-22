from django.contrib import admin
from .models import Patient, Doctor, PillSchedule, PillIntake, PillBoxStatus, Alert

admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(PillSchedule)
admin.site.register(PillIntake)
admin.site.register(PillBoxStatus)
admin.site.register(Alert)
