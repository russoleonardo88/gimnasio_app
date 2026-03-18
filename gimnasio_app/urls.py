from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Aquí es donde conectamos tu app 'alumnos' con el proyecto principal
    path('', include('alumnos.urls')), 
]