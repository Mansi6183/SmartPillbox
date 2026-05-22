from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import VoiceAgentAPI, RefillLogAPI, PatientDeleteView, MQTTScheduleAPI, DispenseViewSet,save_schedule



# Router for viewsets
router = DefaultRouter()
router.register(r'doctors', views.DoctorViewSet)
router.register(r'patients', views.PatientViewSet)
router.register(r'schedules', views.PillScheduleViewSet)
router.register(r'intakes', views.PillIntakeViewSet)
router.register(r'pillbox', views.PillBoxStatusViewSet)
router.register(r'alerts', views.AlertViewSet)
router.register(r'medications', views.MedicationViewSet)
router.register(r'dispense', DispenseViewSet, basename='dispense')

# URL patterns
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('', include(router.urls)),
    path('pill-intake/', views.PillIntakeAPI.as_view(), name='pill-intake'),
    path('refill-status/', views.RefillStatusAPI.as_view(), name='refill-status'),
    path('refill-log/', RefillLogAPI.as_view(), name='refill-log'),
    path('voice-agent/', VoiceAgentAPI.as_view(), name='voice-agent'),
    path('patients/<int:pk>/', PatientDeleteView.as_view(), name='delete-patient'),
    path('schedule/', MQTTScheduleAPI.as_view(), name='mqtt-schedule'),
    path('save-schedule/', views.save_schedule, name='save-schedule'),
]