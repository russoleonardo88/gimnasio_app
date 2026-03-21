from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache # <--- IMPORTANTE
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db import models
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
@never_cache # <--- EVITA QUE EL BOTÓN ATRÁS MUESTRE PROGRESO VIEJO



def dashboard(request):
    alumno = Alumno.objects.filter(user=request.user).first()
    if not alumno:
        if request.user.is_superuser: 
            return redirect('gestion')
        return redirect('login')

    # 1. Cálculo de progreso para las 5 barras (Lunes a Viernes)
    dias_semana = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES']
    progreso_dias = [] # Cambiamos a lista para que sea más fácil de iterar en el template
    
    for dia in dias_semana:
        ejercicios_dia = Ejercicio.objects.filter(alumno=alumno, dia_asignado=dia)
        total = ejercicios_dia.count()
        hechos = ejercicios_dia.filter(completado=True).count()
        porcentaje = int((hechos / total * 100)) if total > 0 else 0
        
        progreso_dias.append({
            'nombre': dia,
            'porcentaje': porcentaje
        })

    # 2. Datos para el gráfico de rendimiento (últimas 5 asistencias)
    asistencias_qs = Asistencia.objects.filter(alumno=alumno).order_by('-fecha')[:5]
    
    # Si no hay datos, enviamos una lista con un 0 para que Chart.js no rompa
    if asistencias_qs.exists():
        grafico_data = [int(a.porcentaje_completado or 0) for a in reversed(asistencias_qs)]
    else:
        grafico_data = [0]# <--- ESTO corrige el error de sintaxis y evita el crash

    # 3. Datos para el gráfico de barras (Días por mes - Ejemplo real)
    # Por ahora, para el build, podés dejarlo estático o calcularlo con Count
    grafico_meses_data = # Ene, Feb, Mar...

    context = {
        'alumno': alumno,
        'progreso_dias': progreso_dias,
        'grafico_rendimiento_data': json.dumps(grafico_data),
        'grafico_dias_data': json.dumps(grafico_meses_data),
        'asistencias': asistencias_qs,
        'mensaje_motivador': "Llevás 3 días esta semana. ¡A darle! 🔥",
    }
    return render(request, 'alumnos/dashboard.html', context)

@login_required
@never_cache
def mi_rutina(request):
    alumno = get_object_or_404(Alumno, user=request.user)
    # Obtenemos el día actual para filtrar automáticamente
    import datetime
    dias_map = {0: 'LUNES', 1: 'MARTES', 2: 'MIERCOLES', 3: 'JUEVES', 4: 'VIERNES', 5: 'VIERNES', 6: 'LUNES'}
    dia_hoy = dias_map[datetime.datetime.now().weekday()]
    
    ejercicios = Ejercicio.objects.filter(alumno=alumno, dia_asignado=dia_hoy)
    
    return render(request, 'alumnos/mi_rutina.html', {
        'alumno': alumno, 
        'ejercicios': ejercicios,
        'dia_nombre': dia_hoy
    })

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
    alumnos_activos = Alumno.objects.filter(es_baja=False) 
    
    if query:
        alumnos_activos = alumnos_activos.filter(
            models.Q(user__first_name__icontains=query) | 
            models.Q(user__last_name__icontains=query) |
            models.Q(codigo__icontains=query)
        )

    context = {
        'alumnos_h': alumnos_activos.filter(genero='H').order_by('user__last_name'),
        'alumnos_m': alumnos_activos.filter(genero='M').order_by('user__last_name'),
        'alumnos_baja': Alumno.objects.filter(es_baja=True).order_by('user__last_name'),
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
            dia_asignado=request.POST.get('dia'),
            categoria=request.POST.get('categoria'),
            sets=request.POST.get('sets', 3),
            reps=request.POST.get('reps', 10),
            peso=request.POST.get('peso', 0)
        )
        return redirect('detalle_alumno', alumno_id=alumno.id)

    ejercicios = Ejercicio.objects.filter(alumno=alumno).order_by('dia_asignado')
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
        # ... lógica de pago ...
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
def recepcion(request):
    return render(request, 'alumnos/recepcion.html')

@login_required
def alta_socio_rapida(request):
    if request.method == 'POST':
        # Aquí va tu lógica de User.objects.create_user y Alumno.objects.create
        return redirect('gestion')
    return render(request, 'alumnos/alta_socio.html')