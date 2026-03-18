from django.urls import path
from . import views

urlpatterns = [
    # --- AUTENTICACIÓN Y PERFIL ---
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/password/', views.cambiar_password, name='cambiar_password'), # <-- RUTA NUEVA
    
    # --- RUTAS PARA EL ALUMNO (App Móvil) ---
    path('dashboard/', views.dashboard_alumno, name='dashboard_alumno'),
    path('mi-rutina/', views.mi_rutina, name='mi_rutina'),
    path('marcar-hecho/<int:ejercicio_id>/', views.marcar_ejercicio_hecho, name='marcar_ejercicio_hecho'),
    
    # --- RUTAS PARA EL ADMIN/DUEÑO (PC Mostrador / Gestión) ---
    path('recepcion/', views.control_acceso, name='control_acceso'),
    path('gestion/', views.gestion_gym, name='gestion_gym'),
    path('gestion/alumno/<int:alumno_id>/', views.detalle_alumno, name='detalle_alumno'),
    path('gestion/editar/<int:alumno_id>/', views.editar_alumno, name='editar_alumno'),
    path('gestion/estado/<int:alumno_id>/', views.cambiar_estado_alumno, name='cambiar_estado_alumno'),
    path('gestion/asistencias/<int:alumno_id>/', views.historial_asistencias, name='historial_asistencias'),
    path('gestion/alta-socio/', views.alta_socio_rapida, name='alta_socio'),
    
    # --- ACCIONES DE RUTINA (ADMIN) ---
    path('alumno/<int:alumno_id>/agregar/', views.agregar_ejercicio_rapido, name='agregar_ejercicio'),
    path('eliminar-ejercicio/<int:ejercicio_id>/', views.eliminar_ejercicio, name='eliminar_ejercicio'),
    path('resetear-rutina/<int:alumno_id>/', views.resetear_rutina, name='resetear_rutina'),
]