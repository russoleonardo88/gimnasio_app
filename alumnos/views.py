from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import Alumno, Ejercicio, Asistencia
from datetime import timedelta

# --- AUTENTICACIÓN ---
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('gestion_gym')
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('gestion_gym')
            return redirect('dashboard')
        else:
            return render(request, 'alumnos/login.html', {'error': 'Usuario o contraseña incorrectos'})

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
    try:
        alumno = Alumno.objects.filter(user=request.user).first()
        
        if not alumno:
            if request.user.is_superuser:
                return redirect('gestion_gym')
            return render(request, 'alumnos/login.html', {'error': 'Tu usuario no tiene un perfil de alumno asignado.'})

        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
        progreso_dias = []
        for dia in dias_semana:
            ejercicios = alumno.ejercicios.filter(dia_semana=dia)
            total = ejercicios.count()
            hechos = ejercicios.filter(completado=True).count()
            porcentaje = int((hechos / total) * 100) if total > 0 else 0
            progreso_dias.append({'nombre': dia, 'porcentaje': porcentaje})

        context = {
            'alumno': alumno,
            'mensaje_motivador': "¡Dale con todo hoy!",
            'progreso_dias': progreso_dias,
            'asistencias': alumno.asistencias.all().order_by('-fecha')[:5],
            'grafico_dias_data': [], 
            'grafico_rendimiento_data': [],
        }
        
        return render(request, 'alumnos/dashboard.html', context)

    except Exception as e:
        print(f"Error en dashboard: {e}")
        return HttpResponse(f"Error interno: {e}", status=500)

@login_required
def mi_rutina(request):
    alumno = Alumno.objects.filter(user=request.user).first()
    if not alumno:
        return redirect('dashboard')

    dia_url = request.GET.get('dia')
    dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    
    dia_nombre = dia_url if dia_url else dias_map[timezone.now().weekday()]
    ejercicios = alumno.ejercicios.filter(dia_semana=dia_nombre)
    
    return render(request, 'alumnos/mi_rutina.html', {'ejercicios': ejercicios, 'dia': dia_nombre})

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

# --- VISTAS DE GESTIÓN (ADMIN) ---
@login_required
def control_acceso(request):
    if not request.user.is_superuser: return redirect('dashboard')
    return render(request, 'alumnos/control_acceso.html')

@login_required
def gestion_gym(request):  # Mantenemos este nombre para que urls.py no explote
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    alumnos_lista = Alumno.objects.all().order_by('user__last_name')
    return render(request, 'alumnos/gestion.html', {'alumnos': alumnos_lista})

@login_required
def detalle_alumno(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    return render(request, 'alumnos/detalle_alumno.html', {'alumno': alumno})

@login_required
def editar_alumno(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    return render(request, 'alumnos/editar_alumno.html', {'alumno': alumno})

@login_required
def cambiar_estado_alumno(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.activo = not alumno.activo
    alumno.save()
    return redirect('gestion_gym')

@login_required
def historial_asistencias(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    return render(request, 'alumnos/historial_asistencias.html', {'alumno': alumno})

@login_required
def alta_socio_rapida(request):
    if not request.user.is_superuser: return redirect('dashboard')
    return render(request, 'alumnos/alta_socio.html')

@login_required
def marcar_pago(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.cuota_pagada = True
    alumno.fecha_vencimiento = timezone.now().date() + timedelta(days=30)
    alumno.save()
    return redirect('detalle_alumno', alumno_id=alumno.id)

@login_required
def agregar_ejercicio_rapido(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    return redirect('detalle_alumno', alumno_id=alumno_id)

@login_required
def eliminar_ejercicio(request, ejercicio_id):
    if not request.user.is_superuser: return redirect('dashboard')
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
    al_id = ejercicio.alumno.id
    ejercicio.delete()
    return redirect('detalle_alumno', alumno_id=al_id)

@login_required
def resetear_rutina(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.ejercicios.all().update(completado=False)
    return redirect('detalle_alumno', alumno_id=alumno_id)

from django.contrib.auth.models import User

def crear_admin_temporal(request):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@test.com', 'admin1234')
        return HttpResponse("Admin creado: usuario 'admin', clave 'admin1234'. ¡BORRÁ ESTO LUEGO!")
    return HttpResponse("El admin ya existe.")