from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/password/', views.cambiar_password, name='cambiar_password'),
    path('dashboard/', views.dashboard, name='dashboard_alumno'),
    path('mi-rutina/', views.mi_rutina, name='mi_rutina'),
    
    # Esta línea se eliminó/comentó porque la función ya no existe en views.py
    # path('marcar-hecho/<int:ejercicio_id>/', views.marcar_ejercicio_hecho, name='marcar_hecho'),
    
    path('recepcion/', views.control_acceso, name='recepcion'),
    path('gestion/', views.gestion_gym, name='gestion_gym'),
    path('gestion/alumno/<int:alumno_id>/', views.detalle_alumno, name='detalle_alumno'),
    path('gestion/editar/<int:alumno_id>/', views.editar_alumno, name='editar_alumno'),
    path('gestion/alta-socio/', views.alta_socio_rapida, name='alta_socio_rapida'),
    path('renovar-cuota/<int:alumno_id>/', views.renovar_cuota, name='renovar_cuota'),
    path('resetear-rutina/<int:alumno_id>/', views.resetear_rutina, name='resetear_rutina'),
    path('eliminar-ejercicio/<int:ejercicio_id>/', views.eliminar_ejercicio, name='eliminar_ejercicio'),
    path('marcar-pago/<int:alumno_id>/', views.marcar_pago, name='marcar_pago'),
    path('cambiar-estado/<int:alumno_id>/', views.cambiar_estado_alumno, name='cambiar_estado_alumno'),
    path('historial/<int:alumno_id>/', views.historial_asistencias, name='historial_asistencias'),
    path('gestion/alumno/<int:alumno_id>/agregar/', views.agregar_ejercicio, name='agregar_ejercicio_v2'),
    
    # ESTA ES LA ÚNICA QUE NECESITAMOS PARA LOS CLICS:
    path('marcar-completado/<int:ejercicio_id>/', views.marcar_completado, name='marcar_completado'),
]