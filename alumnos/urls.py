from django.urls import path
from . import views

urlpatterns = [
    # --- AUTENTICACIÓN Y PERFIL ---
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/password/', views.cambiar_password, name='cambiar_password'),
    
    # --- RUTAS PARA EL ALUMNO (App Móvil) ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mi-rutina/', views.mi_rutina, name='mi_rutina'),
    path('marcar-hecho/<int:ejercicio_id>/', views.marcar_hecho, name='marcar_hecho'),
    
    # --- RUTAS PARA EL ADMIN/DUEÑO (Gestión) ---
    path('recepcion/', views.recepcion, name='recepcion'),
    path('gestion/', views.gestion, name='gestion'),
    path('gestion/alumno/<int:alumno_id>/', views.detalle_alumno, name='detalle_alumno'),
    path('gestion/editar/<int:alumno_id>/', views.editar_alumno, name='editar_alumno'),
    path('gestion/estado/<int:alumno_id>/', views.cambiar_estado_alumno, name='cambiar_estado_alumno'),
    path('gestion/asistencias/<int:alumno_id>/', views.historial_asistencias, name='historial_asistencias'),
    path('gestion/alta-socio/', views.alta_socio_rapida, name='alta_socio_rapida'),
    
    # --- GESTIÓN DE PAGOS Y RUTINA ---
    path('renovar-cuota/<int:alumno_id>/', views.renovar_cuota, name='renovar_cuota'),
    path('resetear-rutina/<int:alumno_id>/', views.resetear_rutina, name='resetear_rutina'),
    path('eliminar-ejercicio/<int:ejercicio_id>/', views.eliminar_ejercicio, name='eliminar_ejercicio'),
    
    # AGREGAMOS ESTA LÍNEA (Es el "alias" para que el HTML no explote)
    path('gestion/alumno/<int:alumno_id>/agregar/', views.detalle_alumno, name='agregar_ejercicio'),
    
    # Unificamos el botón de 'marcar-pago'
    path('marcar-pago/<int:alumno_id>/', views.renovar_cuota, name='marcar_pago'),
]