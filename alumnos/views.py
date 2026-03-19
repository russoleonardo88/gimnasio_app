from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Alumno, Ejercicio, Asistencia, Entrenador
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Avg
from django.db.models.functions import ExtractMonth
from django.contrib import messages
from datetime import timedelta

# --- VISTAS DE AUTENTICACIÓN ---

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                return redirect('gestion_gym')
            return redirect('dashboard_alumno')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

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
            messages.success(request, '¡Contraseña actualizada con éxito!')
            return redirect('dashboard_alumno')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'cambiar_password.html', {'form': form})

# --- VISTAS DEL ALUMNO ---

@login_required
def dashboard_alumno(request):
    try:
        alumno = Alumno.objects.select_related('user').get(user=request.user)
    except Alumno.DoesNotExist:
        if request.user.is_staff:
            return redirect('gestion_gym')
        return render(request, 'dashboard.html', {'error': 'No tienes un perfil de alumno asignado.'})

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    progreso_dias = []
    
    todos_ejercicios = Ejercicio.objects.filter(alumno=alumno)

    for dia in dias_semana:
        ejercicios_dia = todos_ejercicios.filter(dia_semana=dia).all().distinct()
        total = ejercicios_dia.count()
        completados = ejercicios_dia.filter(completado=True).count()
        # Entero para el dashboard
        porcentaje = int((completados / total * 100)) if total > 0 else 0
        progreso_dias.append({'nombre': dia, 'porcentaje': porcentaje})

    traduccion_dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Lunes'
    }
    dia_hoy_esp = traduccion_dias.get(timezone.now().strftime('%A'), 'Lunes')
    ejercicios_hoy = todos_ejercicios.filter(dia_semana=dia_hoy_esp).all().distinct()

    asistencias_recientes = Asistencia.objects.filter(alumno=alumno).order_by('-fecha')[:5]
    hace_una_semana = timezone.now().date() - timedelta(days=7)
    asistencias_semana = Asistencia.objects.filter(alumno=alumno, fecha__gte=hace_una_semana).count()
    
    return render(request, 'dashboard.html', {
        'alumno': alumno, 
        'progreso_dias': progreso_dias, 
        'asistencias': asistencias_recientes,
        'ejercicios_hoy': ejercicios_hoy,
        'mensaje_motivador': f"Llevás {asistencias_semana} días esta semana. ¡A darle! 🔥",
    })

@login_required
def mi_rutina(request):
    traduccion_dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Lunes'
    }
    dia_default = traduccion_dias.get(timezone.now().strftime('%A'), 'Lunes')
    dia_seleccionado = request.GET.get('dia', dia_default)
    alumno = get_object_or_404(Alumno, user=request.user)
    
    ejercicios = Ejercicio.objects.filter(alumno=alumno, dia_semana=dia_seleccionado).all().distinct()
    
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
            
            ejercicios_dia = Ejercicio.objects.filter(alumno=ejercicio.alumno, dia_semana=ejercicio.dia_semana).all().distinct()
            total = ejercicios_dia.count()
            hechos = ejercicios_dia.filter(completado=True).count()
            # Forzamos entero para el progreso de la base de datos
            nuevo_progreso = int((hechos / total * 100)) if total > 0 else 0
            
            asistencia, _ = Asistencia.objects.get_or_create(alumno=ejercicio.alumno, fecha=timezone.now().date())
            asistencia.porcentaje_completado = nuevo_progreso
            asistencia.save()
            
            return JsonResponse({'status': 'ok', 'completado': ejercicio.completado, 'progreso': nuevo_progreso})
        except Ejercicio.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)

# --- VISTAS DE ADMINISTRACIÓN, GESTIÓN Y RECEPCIÓN ---

def control_acceso(request):
    mensaje, clase_alerta, alumno_info = "", "", None
    if request.method == "POST":
        codigo_ingresado = request.POST.get("codigo", "").upper().strip()
        try:
            alumno = Alumno.objects.get(codigo=codigo_ingresado)
            if not alumno.activo:
                mensaje = f"ACCESO DENEGADO: {alumno.user.first_name.upper()} ESTÁ DE BAJA"
                clase_alerta = "danger"
            else:
                Asistencia.objects.get_or_create(alumno=alumno, fecha=timezone.now().date())
                mensaje = f"BIENVENIDO/A {alumno.user.first_name.upper()}!"
                clase_alerta = "success"
                alumno_info = alumno
        except Alumno.DoesNotExist:
            mensaje, clase_alerta = "CÓDIGO NO ENCONTRADO", "warning"
    return render(request, "recepcion.html", {"mensaje": mensaje, "clase_alerta": clase_alerta, "alumno_info": alumno_info})

@login_required
def gestion_gym(request):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    
    # PASO 1: Ordenar alfabéticamente por Apellido (last_name) como en la escuela
    alumnos_activos = Alumno.objects.filter(activo=True).select_related('user').order_by('user__last_name', 'user__first_name')
    alumnos_baja = Alumno.objects.filter(activo=False).select_related('user').order_by('user__last_name')
    
    # Listas para separar hombres y mujeres
    stats_hombres = []
    stats_mujeres = []
    hoy = timezone.now().date()
    
    for alu in alumnos_activos:
        conteo = Asistencia.objects.filter(alumno=alu, fecha__month=hoy.month).count()
        meta = int(alu.plan_semanal) * 4
        
        # Porcentaje de asistencia mensual como entero
        porcentaje_mes = int((conteo / meta * 100)) if meta > 0 else 0
        
        ultima = Asistencia.objects.filter(alumno=alu).order_by('-fecha').first()
        # Progreso de hoy como entero
        progreso_hoy = int(ultima.porcentaje_completado if ultima else 0)
        
        data_alumno = {
            'alumno': alu, 
            'asistencias': conteo, 
            'porcentaje_asistencia': porcentaje_mes,
            'progreso_rutina': progreso_hoy
        }

        # PASO 2: Separar por género
        if alu.genero == 'H':
            stats_hombres.append(data_alumno)
        else:
            stats_mujeres.append(data_alumno)

    return render(request, 'gestion.html', {
        'stats_hombres': stats_hombres, 
        'stats_mujeres': stats_mujeres, 
        'alumnos_baja': alumnos_baja
    })

@login_required
def detalle_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    rutina = {dia: Ejercicio.objects.filter(alumno=alumno, dia_semana=dia).all().distinct() for dia in dias}
    return render(request, 'detalle_alumno.html', {'alumno': alumno, 'rutina': rutina, 'dias': dias})

@login_required
def editar_alumno(request, alumno_id):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    if request.method == "POST":
        alumno.user.first_name = request.POST.get('nombre')
        alumno.user.last_name = request.POST.get('apellido')
        alumno.user.save()
        alumno.plan_semanal = request.POST.get('plan')
        alumno.dni = request.POST.get('dni')
        alumno.domicilio = request.POST.get('domicilio')
        alumno.celular = request.POST.get('celular')
        alumno.contacto_emergencia = request.POST.get('emergencia')
        alumno.save()
        return redirect('gestion_gym')
    return render(request, 'editar_alumno.html', {'alumno': alumno})

@login_required
def agregar_ejercicio_rapido(request, alumno_id):
    if request.method == 'POST':
        alumno = get_object_or_404(Alumno, id=alumno_id)
        timmer_form = request.POST.get('timmer')
        
        Ejercicio.objects.create(
            alumno=alumno,
            nombre=request.POST.get('nombre'),
            tipo=request.POST.get('tipo'),
            dia_semana=request.POST.get('dia'),
            series=request.POST.get('series') or 1,
            repeticiones=request.POST.get('reps'),
            peso_sugerido=request.POST.get('peso') or 0,
            timmer=timmer_form
        )
        return redirect('detalle_alumno', alumno_id=alumno.id)
    return redirect('gestion_gym')

@login_required
def eliminar_ejercicio(request, ejercicio_id):
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
    alu_id = ejercicio.alumno.id
    if request.user.is_staff:
        ejercicio.delete()
    return redirect('detalle_alumno', alumno_id=alu_id)

@login_required
def cambiar_estado_alumno(request, alumno_id):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.activo = not alumno.activo
    alumno.save()
    return redirect('gestion_gym')

@login_required
def alta_socio_rapida(request):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    if request.method == "POST":
        nombre = request.POST.get('nombre').strip()
        apellido = request.POST.get('apellido').strip()
        codigo = request.POST.get('codigo').upper().strip()
        plan = request.POST.get('plan')
        dni = request.POST.get('dni')
        domicilio = request.POST.get('domicilio')
        celular = request.POST.get('celular')
        emergencia = request.POST.get('emergencia')
        
        genero = 'H' if codigo.startswith('H') else 'M'
        user = User.objects.create_user(username=codigo, first_name=nombre, last_name=apellido, password=codigo)
        
        Alumno.objects.create(
            user=user, 
            codigo=codigo, 
            genero=genero, 
            plan_semanal=plan, 
            dni=dni,
            domicilio=domicilio,
            celular=celular,
            contacto_emergencia=emergencia,
            activo=True, 
            fecha_inicio_rutina=timezone.now().date()
        )
        return redirect('gestion_gym')
    return render(request, 'alta_socio.html')

@login_required
def resetear_rutina(request, alumno_id):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    Ejercicio.objects.filter(alumno=alumno).delete()
    alumno.fecha_inicio_rutina = timezone.now().date()
    alumno.save()
    return redirect('gestion_gym')

@login_required
def historial_asistencias(request, alumno_id):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    asistencias = Asistencia.objects.filter(alumno=alumno).order_by('-fecha')
    # Nos aseguramos de que el porcentaje sea entero antes de enviar al template
    for asis in asistencias:
        asis.porcentaje_completado = int(asis.porcentaje_completado)
        
    return render(request, 'historial_asistencias.html', {'alumno': alumno, 'asistencias': asistencias})