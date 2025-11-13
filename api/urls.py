from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import VoiceAgentAPI

# ✅ Define router and register all viewsets
router = DefaultRouter()
router.register(r'doctors', views.DoctorViewSet)
router.register(r'patients', views.PatientViewSet)
router.register(r'schedules', views.PillScheduleViewSet)
router.register(r'intakes', views.PillIntakeViewSet)
router.register(r'pillbox', views.PillBoxStatusViewSet)
router.register(r'alerts', views.AlertViewSet)

# ✅ Define urlpatterns (single list only)
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('', include(router.urls)),
    path('pill-intake/', views.PillIntakeAPI.as_view(), name='pill-intake'),
    path('refill-status/', views.RefillStatusAPI.as_view(), name='refill-status'),
    path('voice-agent/', VoiceAgentAPI.as_view(), name='voice-agent'),
]
