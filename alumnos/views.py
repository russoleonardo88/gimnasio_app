from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Alumno, Ejercicio, Asistencia
from datetime import timedelta

# --- AUTENTICACIÓN ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_alumno')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('dashboard_alumno')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'cambiar_password.html', {'form': form})

@login_required
def dashboard_alumno(request):
    alumno = get_object_or_404(Alumno, user=request.user)
    asistencias = alumno.asistencias.filter(fecha__month=timezone.now().month).count()
    
    context = {
        'alumno': alumno,
        'dias_restantes': alumno.dias_restantes_cuota(),
        'rutina_vencida': alumno.rutina_vencida(),
        'asistencias_mes': asistencias,
        'grafico_asistencia_data': [],  # <-- CORREGIDO
        'grafico_dias_labels': ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    }
    
    return render(request, 'dashboard_alumno.html', context)

@login_required
def mi_rutina(request):
    alumno = get_object_or_404(Alumno, user=request.user)
    dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    dia_nombre = dias_map[timezone.now().weekday()]
    ejercicios = alumno.ejercicios.filter(dia_semana=dia_nombre)
    return render(request, 'mi_rutina.html', {'ejercicios': ejercicios, 'dia': dia_nombre})

@login_required
def marcar_hecho(request, ejercicio_id):
    if request.method == 'POST':
        ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id, alumno__user=request.user)
        ejercicio.completado = not ejercicio.completado
        if ejercicio.completado:
            ejercicio.ultima_vez_hecho = timezone.now()
        ejercicio.save()
        return JsonResponse({'status': 'ok', 'completado': ejercicio.completado})
    return JsonResponse({'status': 'error'}, status=400)

# --- VISTAS DE GESTIÓN ---
@login_required
def control_acceso(request):
    return render(request, 'control_acceso.html')

@login_required
def gestion_gym(request):
    alumnos = Alumno.objects.all()
    return render(request, 'gestion_gym.html', {'alumnos': alumnos})

@login_required
def detalle_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    return render(request, 'detalle_alumno.html', {'alumno': alumno})

@login_required
def editar_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    return render(request, 'editar_alumno.html', {'alumno': alumno})

@login_required
def cambiar_estado_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.activo = not alumno.activo
    alumno.save()
    return redirect('gestion_gym')

@login_required
def historial_asistencias(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    return render(request, 'historial_asistencias.html', {'alumno': alumno})

@login_required
def alta_socio_rapida(request):
    return render(request, 'alta_socio.html')

@login_required
def marcar_pago(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.cuota_pagada = True
    alumno.fecha_vencimiento = timezone.now().date() + timedelta(days=30)
    alumno.save()
    return redirect('detalle_alumno', alumno_id=alumno.id)

@login_required
def agregar_ejercicio_rapido(request, alumno_id):
    return redirect('detalle_alumno', alumno_id=alumno_id)

@login_required
def eliminar_ejercicio(request, ejercicio_id):
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
    al_id = ejercicio.alumno.id
    ejercicio.delete()
    return redirect('detalle_alumno', alumno_id=al_id)

@login_required
def resetear_rutina(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.ejercicios.all().update(completado=False)
    return redirect('detalle_alumno', alumno_id=alumno_id)