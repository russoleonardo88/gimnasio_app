from django.contrib import admin
from django.urls import path, include
from alumnos import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Conectamos las urls de la app alumnos a la raíz del proyecto
    path('', include('alumnos.urls')), 
    path('login/', views.login_usuario, name='login'),
]