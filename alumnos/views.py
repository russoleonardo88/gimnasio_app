import json
import calendar
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
from django.db.models.functions import ExtractMonth
from django.contrib import messages
from datetime import timedelta

# --- VISTAS DE AUTENTICACIÓN ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('gestion_gym' if request.user.is_staff else 'dashboard_alumno')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Recordarme: 1 año o 24hs
            request.session.set_expiry(31536000 if request.POST.get('remember_me') else 86400)
            
            if user.is_staff:
                return redirect('gestion_gym')
            return redirect('dashboard_alumno')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = AuthenticationForm()
    return render(request, 'alumnos/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Importante para no cerrar sesión
            messages.success(request, '¡Tu contraseña fue actualizada con éxito!')
            return redirect('dashboard_alumno') # <--- ASEGURATE QUE DIGA ESTO
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'alumnos/cambiar_password.html', {'form': form})

# --- VISTAS DEL ALUMNO ---
@login_required
def dashboard(request):
    # SEGURIDAD: Staff fuera del dashboard de alumnos
    if request.user.is_staff:
        return redirect('gestion_gym')

    try:
        alumno = Alumno.objects.select_related('user').get(user=request.user)
    except Alumno.DoesNotExist:
        return render(request, 'alumnos/dashboard.html', {
            'error': 'No tienes un perfil de alumno asignado. Contacta al administrador.'
        })

    # =========================================================================
    # RECONSTRUCCIÓN DINÁMICA DE EJERCICIOS Y CHECKS
    # =========================================================================
    hoy = timezone.now()
    
    # 1. Diccionario para traducir el día de hoy (Sábado y Domingo redirigen a Lunes)
    traduccion_dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 
        'Saturday': 'Lunes', 'Sunday': 'Lunes'
    }
    
    # 2. Obtener el día actual en español (ej: "Lunes")
    dia_hoy_esp = traduccion_dias.get(hoy.strftime('%A'), 'Lunes')

    # 3. Filtrar y ordenar los ejercicios de HOY por tipo (para el Grid responsivo)
    # Obtenemos los ejercicios del día actual para mostrarlos uno abajo del otro
    ejercicios_hoy = Ejercicio.objects.filter(
        alumno=alumno, 
        dia_semana=dia_hoy_esp
    ).order_by('tipo') # Ordenar por tipo para que la cuadrícula se vea más organizada

    # =========================================================================
    # LÓGICA DE ESTADÍSTICAS Y GRÁFICOS (Mantenida intacta)
    # =========================================================================

    # --- DATOS PARA DISTRIBUCIÓN DE ENTRENAMIENTO (Dona) ---
    todos_ejercicios = Ejercicio.objects.filter(alumno=alumno)
    ejercicios_hechos = todos_ejercicios.filter(completado=True)
    total_completados = ejercicios_hechos.count()

    if total_completados > 0:
        c_fuerza = ejercicios_hechos.filter(tipo='FUERZA').count()
        c_aero = ejercicios_hechos.filter(tipo='AEROBICO').count()
        p_fuerza = round((c_fuerza / total_completados) * 100)
        p_aero = round((c_aero / total_completados) * 100)
    else:
        p_fuerza, p_aero = 0, 0

    datos_distribucion = [p_fuerza, p_aero]

    # --- DATOS PARA RENDIMIENTO POR SEMANA (Línea) ---
    rendimiento = []
    _, ultimo_dia = calendar.monthrange(hoy.year, hoy.month)

    semanas = [
        (1, 7), (8, 14), (15, 21), (22, ultimo_dia)
    ]

    for inicio, fin in semanas:
        ejercicios_semana = Ejercicio.objects.filter(
            alumno=alumno,
            fecha_asignacion__year=hoy.year,
            fecha_asignacion__month=hoy.month,
            fecha_asignacion__day__gte=inicio,
            fecha_asignacion__day__lte=fin
        )

        asignados = ejercicios_semana.count()
        realizados = ejercicios_semana.filter(completado=True).count()

        if asignados > 0:
            porcentaje = round((realizados / asignados) * 100)
        else:
            porcentaje = 0

        rendimiento.append(porcentaje)

    # Lógica de progreso semanal que ya tenías (ej: Llevás 4 días esta semana)
    hace_una_semana = hoy.date() - timedelta(days=7)
    asistencias_semana = Asistencia.objects.filter(alumno=alumno, fecha__gte=hace_una_semana).count()

    return render(request, 'alumnos/dashboard.html', {
        'datos_distribucion': json.dumps(datos_distribucion), 
        'rendimiento': json.dumps(rendimiento),
        'alumno': alumno,
        'dia_hoy_esp': dia_hoy_esp, # Pasamos el día actual para el título
        'ejercicios_hoy': ejercicios_hoy, # Pasamos la lista de ejercicios del día
        'asistencias_semana': asistencias_semana,
        'mensaje_motivador': f"Llevás {asistencias_semana} días esta semana. ¡A darle! 🔥",
    })



@login_required
def mi_rutina(request):
    traduccion_dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 
        'Saturday': 'Lunes', 'Sunday': 'Lunes'
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

    return render(request, 'alumnos/mi_rutina.html', {'ejercicios': ejercicios, 'dia': dia_seleccionado, 'alumno': alumno})

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
            hechos = ejercicios_dia.filter(completado=True).count()
            nuevo_progreso = int((hechos / total * 100)) if total > 0 else 0
            
            asistencia, _ = Asistencia.objects.get_or_create(alumno=ejercicio.alumno, fecha=timezone.now().date())
            asistencia.porcentaje_completado = nuevo_progreso
            asistencia.save()
            
            return JsonResponse({'status': 'ok', 'completado': ejercicio.completado, 'progreso': nuevo_progreso})
        except Ejercicio.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)

# --- VISTAS DE ADMINISTRACIÓN Y GESTIÓN ---

def control_acceso(request):
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
        except Alumno.MultipleObjectsReturned:
            mensaje, clase_alerta = "ERROR: DNI DUPLICADO EN SISTEMA", "danger"
            
    return render(request, "alumnos/recepcion.html", {"mensaje": mensaje, "clase_alerta": clase_alerta, "alumno_info": alumno_info})

@login_required
def gestion_gym(request):
    if not request.user.is_staff:
        return redirect('dashboard_alumno')
    
    hoy = timezone.now().date()
    alumnos_activos = Alumno.objects.filter(activo=True).select_related('user')
    alumnos_baja = Alumno.objects.filter(activo=False).select_related('user')
    
    stats_hombres = []
    stats_mujeres = []
    
    traduccion_dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 
        'Saturday': 'Lunes', 'Sunday': 'Lunes'
    }
    dia_hoy = traduccion_dias.get(timezone.now().strftime('%A'), 'Lunes')

    for alu in alumnos_activos:
        # 1. Porcentaje de asistencia mensual (Base: Plan semanal * 4 semanas)
        conteo_mes = Asistencia.objects.filter(alumno=alu, fecha__month=hoy.month).count()
        meta_mes = (alu.plan_semanal or 0) * 4
        porcentaje_asistencia = int((conteo_mes / meta_mes * 100)) if meta_mes > 0 else 0
        
        # 2. Progreso de rutina de HOY
        ejercicios_hoy = Ejercicio.objects.filter(alumno=alu, dia_semana=dia_hoy).distinct()
        total_hoy = ejercicios_hoy.count()
        hechos_hoy = ejercicios_hoy.filter(completado=True).count()
        progreso_hoy = int((hechos_hoy / total_hoy * 100)) if total_hoy > 0 else 0

        # 3. Estado de cuota
        c_color = '#98cf2c' if alu.cuota_pagada else '#ff4d4d'
        c_estado = 'PAGADO' if alu.cuota_pagada else 'PENDIENTE'

        data = {
            'alumno': alu,
            'porcentaje_asistencia': porcentaje_asistencia,
            'progreso_rutina': progreso_hoy,
            'cuota_estado': c_estado,
            'cuota_color': c_color,
        }
        
        if alu.genero == 'H':
            stats_hombres.append(data)
        else:
            stats_mujeres.append(data)
            
    return render(request, 'alumnos/gestion.html', {
        'stats_hombres': stats_hombres,
        'stats_mujeres': stats_mujeres,
        'alumnos_baja': alumnos_baja
    })

@login_required
def detalle_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    rutina = {dia: Ejercicio.objects.filter(alumno=alumno, dia_semana=dia).distinct() for dia in dias}
    return render(request, 'alumnos/detalle_alumno.html', {'alumno': alumno, 'rutina': rutina, 'dias': dias})

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
        alumno.cuota_pagada = 'cuota_pagada' in request.POST
        alumno.save()
        messages.success(request, f"Datos de {alumno.user.first_name} actualizados.")
        return redirect('gestion_gym')
    return render(request, 'alumnos/editar_alumno.html', {'alumno': alumno})

@login_required
def marcar_pago(request, alumno_id):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.cuota_pagada = True
    alumno.save()
    messages.success(request, f"Pago registrado para {alumno.user.first_name}.")
    return redirect('gestion_gym')

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
            peso_sugerido=request.POST.get('peso') or 0,
            timmer=request.POST.get('timmer')
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
            user=user, codigo=codigo, genero=genero, plan_semanal=plan, 
            dni=dni, domicilio=domicilio, celular=celular,
            contacto_emergencia=emergencia, activo=True, 
            fecha_inicio_rutina=timezone.now().date()
        )
        return redirect('gestion_gym')
    return render(request, 'alumnos/alta_socio.html')

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
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    asistencias = Asistencia.objects.filter(alumno=alumno, fecha__range=[hace_30_dias, hoy]).order_by('-fecha')
    
    conteo = Asistencia.objects.filter(alumno=alumno, fecha__month=hoy.month, fecha__year=hoy.year).count()
    meta = int(alumno.plan_semanal or 0) * 4
    porcentaje_mes = int((conteo / meta * 100)) if meta > 0 else 0
    
    return render(request, 'alumnos/historial_asistencias.html', {
        'alumno': alumno, 
        'asistencias': asistencias,
        'porcentaje_mes': porcentaje_mes,
    })

@login_required
def renovar_cuota(request, alumno_id):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.cuota_pagada = True
    alumno.fecha_pago = timezone.now().date()
    alumno.save()
    return redirect('gestion_gym')

# Agregá esto al final de alumnos/views.py si no existe
@login_required
def agregar_ejercicio(request, alumno_id):
    if request.method == 'POST':
        alumno = get_object_or_404(Alumno, id=alumno_id)
        
        # Corregimos 'dia' por 'dia_semana' para que coincida con tu modelo
        Ejercicio.objects.create(
            alumno=alumno,
            nombre=request.POST.get('nombre'),
            tipo=request.POST.get('tipo'),
            dia_semana=request.POST.get('dia'), # <--- Aquí estaba el error
            series=request.POST.get('series') or 0,
            repeticiones=request.POST.get('reps') or "0", # Usamos 'reps' que es lo que manda tu HTML
            peso_sugerido=request.POST.get('peso') or 0
        )
        messages.success(request, "Ejercicio agregado correctamente.")
    return redirect('detalle_alumno', alumno_id=alumno_id)