from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count
from .models import Alumno, Ejercicio, Asistencia, Entrenador
from datetime import timedelta, date

# --- AUTENTICACIÓN ---
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('gestion')
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('gestion')
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
                return redirect('gestion')
            return render(request, 'alumnos/login.html', {'error': 'Perfil no encontrado.'})

        # 1. Progreso por día
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        progreso_dias = []
        for dia in dias_semana:
            ejercicios = alumno.ejercicios.filter(dia_semana=dia)
            total = ejercicios.count()
            hechos = ejercicios.filter(completado=True).count()
            porcentaje = int((hechos / total) * 100) if total > 0 else 0
            progreso_dias.append({'nombre': dia, 'porcentaje': porcentaje})

        # 2. Datos para Gráficos
        ultimas_asistencias = Asistencia.objects.filter(alumno=alumno).order_by('-fecha')[:5]
        # Cambiamos la lógica para evitar que total_asistencias sea indefinida
        total_asistencias_cuenta = Asistencia.objects.filter(alumno=alumno).count()
        
        grafico_rendimiento_data = [int(a.porcentaje_completado if hasattr(a, 'porcentaje_completado') else 0) for a in reversed(ultimas_asistencias)]
        
        if not grafico_rendimiento_data:
            # Ponemos datos de respaldo basados en la cuenta real
            grafico_rendimiento_data = [total_asistencias_cuenta, 0]

        context = {
            'alumno': alumno,
            'mensaje_motivador': "¡DALE CON TODO HOY!",
            'progreso_dias': progreso_dias,
            'asistencias': ultimas_asistencias,
            'grafico_rendimiento_data': grafico_rendimiento_data,
        }
        
        return render(request, 'alumnos/dashboard.html', context)

    except Exception as e:
        return HttpResponse(f"Error en Dashboard: {e}", status=500)

@login_required
def mi_rutina(request):
    alumno = get_object_or_404(Alumno, user=request.user)
    dia_url = request.GET.get('dia')
    dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    dia_nombre = dia_url if dia_url else dias_map[timezone.now().weekday()]
    ejercicios = alumno.ejercicios.filter(dia_semana=dia_nombre)
    
    context = {
        'ejercicios': ejercicios,
        'dia': dia_nombre,
        'any_aerobico': ejercicios.filter(tipo__in=['AERÓBICO', 'AEROBICO']).exists(),
        'any_fuerza': ejercicios.filter(tipo='FUERZA').exists(),
        'any_zona_media': ejercicios.filter(tipo__in=['ZONA_MEDIA', 'ZONA MEDIA', 'TABATA']).exists(),
    }
    return render(request, 'alumnos/mi_rutina.html', context)

@login_required
def marcar_hecho(request, ejercicio_id):
    if request.method == 'POST':
        ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id, alumno__user=request.user)
        ejercicio.completado = not ejercicio.completado
        if ejercicio.completado:
            ejercicio.ultima_vez_hecho = timezone.now()
        ejercicio.save()
        
        ejercicios_dia = Ejercicio.objects.filter(alumno=ejercicio.alumno, dia_semana=ejercicio.dia_semana)
        total = ejercicios_dia.count()
        hechos = ejercicios_dia.filter(completado=True).count()
        porcentaje = int((hechos / total) * 100) if total > 0 else 0
        
        return JsonResponse({'status': 'ok', 'completado': ejercicio.completado, 'nuevo_porcentaje': porcentaje})
    return JsonResponse({'status': 'error'}, status=400)

# --- VISTAS DE GESTIÓN (ADMIN) ---
@login_required
def gestion(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    alumnos_h = Alumno.objects.filter(genero='H', activo=True).order_by('user__last_name')
    alumnos_m = Alumno.objects.filter(genero='M', activo=True).order_by('user__last_name')
    alumnos_baja = Alumno.objects.filter(activo=False).order_by('user__last_name')

    hoy = date.today()
    DIAS_LABORABLES = 20 

    for lista in [alumnos_h, alumnos_m]:
        for alumno in lista:
            asistencias_mes = Asistencia.objects.filter(
                alumno=alumno, 
                fecha__month=hoy.month, 
                fecha__year=hoy.year
            ).count()
            porcentaje = int((asistencias_mes / DIAS_LABORABLES) * 100)
            alumno.porcentaje_mes = min(porcentaje, 100)

    return render(request, 'alumnos/gestion.html', {
        'alumnos_h': alumnos_h,
        'alumnos_m': alumnos_m,
        'alumnos_baja': alumnos_baja,
    })

# --- ESTA ES LA FUNCIÓN QUE RENDER NO ENCONTRABA ---
@login_required
def recepcion(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    mensaje = None
    if request.method == 'POST':
        identificador = request.POST.get('identificador')
        alumno = Alumno.objects.filter(dni=identificador).first() or Alumno.objects.filter(codigo=identificador).first()
        
        if alumno:
            Asistencia.objects.create(alumno=alumno)
            mensaje = f"¡Bienvenido {alumno.user.first_name}!"
        else:
            mensaje = "Socio no encontrado."

    return render(request, 'alumnos/recepcion.html', {'mensaje': mensaje})

@login_required
def historial_asistencias(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    asistencias = alumno.asistencias.all().order_by('-fecha')
    total_asistencias = asistencias.count()
    porcentaje_total = min(int((total_asistencias / 48) * 100), 100) 

    return render(request, 'alumnos/historial_asistencias.html', {
        'alumno': alumno, 
        'asistencias': asistencias,
        'porcentaje_total': porcentaje_total,
        'asistencias_count': total_asistencias
    })

@login_required
def detalle_alumno(request, alumno_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    alumno = get_object_or_404(Alumno, id=alumno_id)
    
    # 1. Lógica para que el botón "Cargar a la rutina" funcione
    if request.method == 'POST':
        Ejercicio.objects.create(
            alumno=alumno,
            nombre=request.POST.get('nombre'),
            dia_semana=request.POST.get('dia_semana'),
            tipo=request.POST.get('tipo', 'FUERZA'),
            sets=request.POST.get('sets', '3'),
            reps=request.POST.get('reps', '12'),
            peso=request.POST.get('peso', '0')
        )
        return redirect('detalle_alumno', alumno_id=alumno.id)

    # 2. Traducimos los nombres para que card_ejercicio.html los entienda
    ejercicios = alumno.ejercicios.all()
    for ej in ejercicios:
        # Adaptamos lo que pide el HTML a lo que tiene la Base de Datos
        ej.series = ej.sets           
        ej.repeticiones = ej.reps     
        ej.peso_sugerido = ej.peso    

    # 3. Organizamos los días
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    rutina_por_dia = {dia: ejercicios.filter(dia_semana=dia) for dia in dias}

    # 4. Calculamos asistencias y PORCENTAJE (Aquí estaba el error 500)
    total_asistencias = alumno.asistencias.count()
    # Calculamos el porcentaje sobre 20 días o lo que prefieras
    porcentaje_total = min(int((total_asistencias / 20) * 100), 100) if total_asistencias > 0 else 0

    context = {
        'alumno': alumno,
        'rutina_por_dia': rutina_por_dia,
        'grafico_rendimiento_data': [total_asistencias, porcentaje_total],
        'total_asistencias': total_asistencias,
        'porcentaje_total': porcentaje_total, # Esta variable faltaba en tu código
    }
    return render(request, 'alumnos/detalle_alumno.html', context)

@login_required
def alta_socio_rapida(request):
    if not request.user.is_superuser: return redirect('dashboard')
    return render(request, 'alumnos/alta_socio.html')

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
    return redirect('gestion')

@login_required
def renovar_cuota(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    base_fecha = max(alumno.fecha_vencimiento or date.today(), date.today())
    alumno.fecha_vencimiento = base_fecha + timedelta(days=30)
    alumno.save()
    return redirect('detalle_alumno', alumno_id=alumno.id)

@login_required
def resetear_rutina(request, alumno_id):
    if not request.user.is_superuser: return redirect('dashboard')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.ejercicios.all().update(completado=False)
    return redirect('detalle_alumno', alumno_id=alumno.id)

@login_required
def eliminar_ejercicio(request, ejercicio_id):
    if not request.user.is_superuser: return redirect('dashboard')
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
    al_id = ejercicio.alumno.id
    ejercicio.delete()
    return redirect('detalle_alumno', alumno_id=al_id)