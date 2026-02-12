from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import VoiceAgentAPI, RefillLogAPI ,PatientDeleteView, MQTTScheduleAPI # 👈 Added RefillLogAPI import

# ✅ Define router and register all viewsets
router = DefaultRouter()
router.register(r'doctors', views.DoctorViewSet)
router.register(r'patients', views.PatientViewSet)
router.register(r'schedules', views.PillScheduleViewSet)
router.register(r'intakes', views.PillIntakeViewSet)
router.register(r'pillbox', views.PillBoxStatusViewSet)
router.register(r'alerts', views.AlertViewSet)
router.register(r'medications', views.MedicationViewSet)


# ✅ Define urlpatterns (single list only)
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('', include(router.urls)),
    path('pill-intake/', views.PillIntakeAPI.as_view(), name='pill-intake'),
    path('refill-status/', views.RefillStatusAPI.as_view(), name='refill-status'),
    path('refill-log/', RefillLogAPI.as_view(), name='refill-log'),  # 👈 Added new POST endpoint
    path('voice-agent/', VoiceAgentAPI.as_view(), name='voice-agent'),
    path('patients/<int:pk>/', PatientDeleteView.as_view(), name='delete-patient'),
    path('dispense/', views.dispense, name='dispense'),

    path("schedule/", MQTTScheduleAPI.as_view(), name="mqtt-schedule"),

    

]

