from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('pilltracker_backend.api.urls')),  # ✅ full path to your api.urls
    path('', lambda request: HttpResponse("✅ Django Backend Running Successfully")),
    path('api-auth/', include('rest_framework.urls')), 
]