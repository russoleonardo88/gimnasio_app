from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import HttpResponse
from .models import Alumno, Asistencia, Ejercicio
from datetime import date, timedelta
import json

# --- AUTENTICACIÓN ---
def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            return redirect('dashboard' if not user.is_superuser else 'gestion')
        return render(request, 'alumnos/login.html', {'error': 'Credenciales inválidas'})
    return render(request, 'alumnos/login.html')

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
            return redirect('dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'alumnos/cambiar_password.html', {'form': form})

# --- VISTAS DEL ALUMNO ---
@login_required
def dashboard(request):
    alumno = Alumno.objects.filter(user=request.user).first()
    if not alumno:
        if request.user.is_superuser: return redirect('gestion')
        return redirect('login')

    asistencias = Asistencia.objects.filter(alumno=alumno).order_by('-fecha')[:5]
    
    # Corregido: Generación de datos para el gráfico
    grafico_data = [int(a.porcentaje_completado) for a in reversed(asistencias)]
    if not grafico_data: grafico_data =0

    context = {
        'alumno': alumno,
        'asistencias': asistencias,
        'grafico_rendimiento_data': json.dumps(grafico_data),
    }
    return render(request, 'alumnos/dashboard.html', context)

@login_required
def mi_rutina(request):
    alumno = get_object_or_404(Alumno, user=request.user)
    ejercicios = alumno.ejercicios.all().order_by('dia_semana')
    return render(request, 'alumnos/mi_rutina.html', {'alumno': alumno, 'ejercicios': ejercicios})

@login_required
def marcar_hecho(request, ejercicio_id):
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id, alumno__user=request.user)
    ejercicio.completado = not ejercicio.completado
    ejercicio.save()
    return redirect('mi_rutina')

# --- VISTAS DE GESTIÓN (ADMIN) ---
@login_required
def gestion(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    query = request.GET.get('q')
    # Filtramos por alumnos activos e inactivos
    alumnos_activos = Alumno.objects.filter(es_baja=False) 
    
    if query:
        alumnos_activos = alumnos_activos.filter(
            models.Q(user__first_name__icontains=query) | 
            models.Q(codigo__icontains=query)
        )

    context = {
        'alumnos_h': alumnos_activos.filter(genero='H').order_by('user__first_name'),
        'alumnos_m': alumnos_activos.filter(genero='M').order_of('user__first_name'),
        'alumnos_baja': Alumno.objects.filter(es_baja=True),
    }
    return render(request, 'alumnos/gestion.html', context)

@login_required
def detalle_alumno(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    
    if request.method == 'POST':
        Ejercicio.objects.create(
            alumno=alumno,
            nombre=request.POST.get('nombre'),
            dia_semana=request.POST.get('dia'),
            series_reps=f"{request.POST.get('series')}x{request.POST.get('reps')}",
            peso=request.POST.get('peso', '0')
        )
        return redirect('detalle_alumno', alumno_id=alumno.id)

    ejercicios = alumno.ejercicios.all().order_by('dia_semana')
    return render(request, 'alumnos/detalle_alumno.html', {'alumno': alumno, 'ejercicios': ejercicios})

@login_required
def editar_alumno(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    if request.method == 'POST':
        alumno.user.first_name = request.POST.get('nombre')
        alumno.user.last_name = request.POST.get('apellido')
        alumno.user.save()
        alumno.dni = request.POST.get('dni')
        alumno.celular = request.POST.get('celular')
        alumno.plan_semanal = request.POST.get('plan')
        if request.POST.get('cuota_pagada'):
            alumno.fecha_vencimiento = date.today() + timedelta(days=30)
            alumno.cuota_pagada = True
        alumno.save()
        return redirect('detalle_alumno', alumno_id=alumno.id)
    return render(request, 'alumnos/editar_alumno.html', {'alumno': alumno})

@login_required
def eliminar_ejercicio(request, ejercicio_id):
    ej = get_object_or_404(Ejercicio, id=ejercicio_id)
    aid = ej.alumno.id
    ej.delete()
    return redirect('detalle_alumno', alumno_id=aid)

@login_required
def renovar_cuota(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.fecha_vencimiento = date.today() + timedelta(days=30)
    alumno.cuota_pagada = True
    alumno.save()
    return redirect('detalle_alumno', alumno_id=alumno.id)

@login_required
def resetear_rutina(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.ejercicios.update(completado=False)
    return redirect('detalle_alumno', alumno_id=alumno.id)

@login_required
def recepcion(request):
    return render(request, 'alumnos/recepcion.html')

@login_required
def alta_socio_rapida(request):
    if request.method == 'POST':
        # Lógica de creación de usuario omitida por brevedad, asumiendo que ya la tienes
        return redirect('gestion')
    return render(request, 'alumnos/alta_socio.html')