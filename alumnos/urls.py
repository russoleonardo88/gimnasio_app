from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('mi-rutina/', views.mi_rutina, name='mi_rutina'),
    path('dashboard/', views.dashboard_alumno, name='dashboard_alumno'),
    path('logout/', views.logout_view, name='logout'),
    
    # ESTA ES LA LÍNEA CLAVE NUEVA:
    path('marcar-hecho/<int:ejercicio_id>/', views.marcar_ejercicio_hecho, name='marcar_hecho'),
]