from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Alumno, Ejercicio, Asistencia, Entrenador
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.contrib import messages
from datetime import timedelta, datetime

# --- VISTAS DE ALUMNO (OPTIMIZADAS) ---

@login_required
def dashboard_alumno(request):
    try:
        alumno = Alumno.objects.select_related('user').get(user=request.user)
    except Alumno.DoesNotExist:
        if request.user.is_staff: return redirect('gestion_gym')
        return render(request, 'dashboard.html', {'error': 'No tienes un perfil asignado.'})

    hoy = timezone.now().date()
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    progreso_dias = []
    
    todos_ejercicios = Ejercicio.objects.filter(alumno=alumno)

    for dia in dias_semana:
        ejercicios_dia = todos_ejercicios.filter(dia_semana=dia).distinct()
        total = ejercicios_dia.count()
        completados = ejercicios_dia.filter(completado=True, ultima_vez_hecho__date=hoy).count()
        
        porcentaje = int((completados / total * 100)) if total > 0 else 0
        progreso_dias.append({'nombre': dia, 'porcentaje': porcentaje})

    # Lógica de Gráficos
    grafico_dias_data = []
    for i in range(5, -1, -1):
        fecha_aux = hoy - timedelta(days=i*30)
        conteo = Asistencia.objects.filter(
            alumno=alumno, 
            fecha__month=fecha_aux.month, 
            fecha__year=fecha_aux.year
        ).count()
        grafico_dias_data.append(conteo)

    grafico_rendimiento_data = []
    for i in range(3, -1, -1):
        inicio_semana = hoy - timedelta(days=hoy.weekday() + (i*7))
        fin_semana = inicio_semana + timedelta(days=6)
        rendimiento_medio = Asistencia.objects.filter(
            alumno=alumno, 
            fecha__range=[inicio_semana, fin_semana]
        ).aggregate(Avg('porcentaje_completado'))['porcentaje_completado__avg'] or 0
        grafico_rendimiento_data.append(int(rendimiento_medio))

    asistencias_recientes = Asistencia.objects.filter(alumno=alumno).order_by('-fecha')[:5]
    asistencias_semana = Asistencia.objects.filter(alumno=alumno, fecha__gte=hoy - timedelta(days=7)).count()
    
    return render(request, 'dashboard.html', {
        'alumno': alumno, 
        'progreso_dias': progreso_dias, 
        'asistencias': asistencias_recientes,
        'grafico_dias_data': grafico_dias_data,
        'grafico_rendimiento_data': grafico_rendimiento_data,
        'mensaje_motivador': f"Llevás {asistencias_semana} días esta semana. ¡Dale con todo! 🔥",
    })

@login_required
def mi_rutina(request):
    traduccion_dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Lunes', 'Sunday': 'Lunes'
    }
    dia_default = traduccion_dias.get(timezone.now().strftime('%A'), 'Lunes')
    dia_seleccionado = request.GET.get('dia', dia_default)
    alumno = get_object_or_404(Alumno, user=request.user)
    
    ejercicios = Ejercicio.objects.filter(alumno=alumno, dia_semana=dia_seleccionado).distinct()
    hoy = timezone.now().date()
    
    for ej in ejercicios:
        if ej.ultima_vez_hecho and ej.ultima_vez_hecho.date() < hoy:
            ej.completado = False
            ej.save()

    return render(request, 'mi_rutina.html', {'ejercicios': ejercicios, 'dia': dia_seleccionado, 'alumno': alumno})

@csrf_exempt
@login_required
def marcar_ejercicio_hecho(request, ejercicio_id):
    if request.method == 'POST':
        try:
            ejercicio = Ejercicio.objects.get(id=ejercicio_id, alumno__user=request.user)
            ejercicio.completado = not ejercicio.completado
            ejercicio.ultima_vez_hecho = timezone.now()
            ejercicio.save()
            
            ejercicios_dia = Ejercicio.objects.filter(alumno=ejercicio.alumno, dia_semana=ejercicio.dia_semana).distinct()
            total = ejercicios_dia.count()
            hechos = ejercicios_dia.filter(completado=True, ultima_vez_hecho__date=timezone.now().date()).count()
            nuevo_progreso = int((hechos / total * 100)) if total > 0 else 0
            
            asistencia, _ = Asistencia.objects.get_or_create(alumno=ejercicio.alumno, fecha=timezone.now().date())
            asistencia.porcentaje_completado = nuevo_progreso
            asistencia.save()
            
            return JsonResponse({'status': 'ok', 'completado': ejercicio.completado, 'progreso': nuevo_progreso})
        except Ejercicio.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)

# --- VISTAS DE GESTIÓN Y ADMINISTRACIÓN ---

@login_required
def control_acceso(request):
    if not request.user.is_staff:
        return redirect('dashboard_alumno')
        
    mensaje, clase_alerta, alumno_info = "", "", None
    if request.method == "POST":
        dato_ingresado = request.POST.get("codigo", "").upper().strip()
        try:
            alumno = Alumno.objects.get(Q(codigo=dato_ingresado) | Q(dni=dato_ingresado))
            if not alumno.activo:
                mensaje = f"ACCESO DENEGADO: {alumno.user.first_name.upper()} ESTÁ DE BAJA"
                clase_alerta = "danger"
            else:
                Asistencia.objects.get_or_create(alumno=alumno, fecha=timezone.now().date())
                mensaje = f"BIENVENIDO/A {alumno.user.first_name.upper()}!"
                clase_alerta = "success"
                alumno_info = alumno
        except Alumno.DoesNotExist:
            mensaje, clase_alerta = "CÓDIGO O DNI NO ENCONTRADO", "warning"
            
    return render(request, "recepcion.html", {"mensaje": mensaje, "clase_alerta": clase_alerta, "alumno_info": alumno_info})

@login_required
def editar_alumno(request, alumno_id):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    if request.method == 'POST':
        alumno.user.first_name = request.POST.get('nombre')
        alumno.user.last_name = request.POST.get('apellido')
        alumno.dni = request.POST.get('dni')
        alumno.telefono = request.POST.get('telefono')
        alumno.user.save()
        alumno.save()
        messages.success(request, "Alumno actualizado.")
        return redirect('detalle_alumno', alumno_id=alumno.id)
    return render(request, 'editar_alumno.html', {'alumno': alumno})

@login_required
def nuevo_alumno(request):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    if request.method == 'POST':
        return redirect('gestion_gym') # Lógica simplificada para evitar errores
    return render(request, 'nuevo_alumno.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('gestion_gym' if request.user.is_staff else 'dashboard_alumno')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            request.session.set_expiry(31536000 if request.POST.get('remember_me') else 86400)
            return redirect('gestion_gym' if user.is_staff else 'dashboard_alumno')
        messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, 'login.html', {'form': AuthenticationForm()})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def gestion_gym(request):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    hoy = timezone.now().date()
    alumnos_activos = Alumno.objects.filter(activo=True).select_related('user').order_by('user__last_name')
    
    stats_hombres, stats_mujeres = [], []
    for alu in alumnos_activos:
        conteo = Asistencia.objects.filter(alumno=alu, fecha__month=hoy.month, fecha__year=hoy.year).count()
        ultima = Asistencia.objects.filter(alumno=alu).order_by('-fecha').first()
        progreso = int(ultima.porcentaje_completado if (ultima and ultima.fecha == hoy) else 0)
        
        data = {'alumno': alu, 'asistencias': conteo, 'progreso_rutina': progreso}
        if alu.genero == 'H': stats_hombres.append(data)
        else: stats_mujeres.append(data)
            
    return render(request, 'gestion.html', {
        'stats_hombres': stats_hombres, 
        'stats_mujeres': stats_mujeres, 
        'alumnos_baja': Alumno.objects.filter(activo=False)
    })

@login_required
def detalle_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    rutina = {dia: Ejercicio.objects.filter(alumno=alumno, dia_semana=dia).distinct() for dia in dias}
    return render(request, 'detalle_alumno.html', {'alumno': alumno, 'rutina': rutina, 'dias': dias})

@login_required
def agregar_ejercicio_rapido(request, alumno_id):
    if request.method == 'POST':
        alumno = get_object_or_404(Alumno, id=alumno_id)
        Ejercicio.objects.create(
            alumno=alumno,
            nombre=request.POST.get('nombre'),
            tipo=request.POST.get('tipo'),
            dia_semana=request.POST.get('dia'),
            series=request.POST.get('series') or 1,
            repeticiones=request.POST.get('reps'),
            peso_sugerido=request.POST.get('peso') or 0
        )
        return redirect('detalle_alumno', alumno_id=alumno.id)
    return redirect('gestion_gym')

@login_required
def eliminar_ejercicio(request, ejercicio_id):
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
    alu_id = ejercicio.alumno.id
    ejercicio.delete()
    return redirect('detalle_alumno', alumno_id=alu_id)

@login_required
def cambiar_estado_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.activo = not alumno.activo
    alumno.save()
    return redirect('gestion_gym')

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('dashboard_alumno')
    return render(request, 'cambiar_password.html', {'form': PasswordChangeForm(request.user)})