import json
import calendar
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.db.models.functions import ExtractMonth
from django.contrib import messages

from .models import Alumno, Ejercicio, Asistencia, Entrenador

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
            update_session_auth_hash(request, user)
            messages.success(request, '¡Tu contraseña fue actualizada con éxito!')
            return redirect('dashboard_alumno')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'alumnos/cambiar_password.html', {'form': form})

# --- VISTAS DEL ALUMNO ---

@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('gestion_gym')

    try:
        alumno = Alumno.objects.select_related('user').get(user=request.user)
    except Alumno.DoesNotExist:
        # Importante: Asegúrate de tener 'alumnos/dashboard.html' o la ruta correcta
        return render(request, 'alumnos/dashboard.html', {'error': 'Perfil no encontrado.'})

    hoy = timezone.now()
    traduccion_dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    dia_hoy_esp = traduccion_dias.get(hoy.strftime('%A'), 'Lunes')
    
    todos_ejercicios = Ejercicio.objects.filter(alumno=alumno)
    ejercicios_hoy = todos_ejercicios.filter(dia_semana=dia_hoy_esp).distinct()
    
    total_hoy = ejercicios_hoy.count()
    completados_hoy = ejercicios_hoy.filter(completado=True).count()
    progreso_hoy = int((completados_hoy / total_hoy * 100)) if total_hoy > 0 else 0

    # --- LÓGICA GRÁFICO DE DISTRIBUCIÓN (Dona) ---
    ejercicios_completados_hoy = ejercicios_hoy.filter(completado=True)

    if not ejercicios_completados_hoy.exists():
        datos_distribucion =
    else:
        total_c = ejercicios_completados_hoy.count()
        # Usamos los nombres de tipos que tengas en tu modelo (ej: 'FUERZA', 'AEROBICO', 'ZONA_MEDIA')
        p_fuerza = round((ejercicios_completados_hoy.filter(tipo='FUERZA').count() / total_c) * 100)
        p_aero = round((ejercicios_completados_hoy.filter(tipo='AEROBICO').count() / total_c) * 100)
        p_media = round((ejercicios_completados_hoy.filter(tipo='ZONA_MEDIA').count() / total_c) * 100)
        datos_distribucion = [p_fuerza, p_aero, p_media]
    
    # --- LÓGICA GRÁFICO DE RENDIMIENTO SEMANAL (Línea) ---
    rendimiento = []
    _, ultimo_dia = calendar.monthrange(hoy.year, hoy.month)
    # Definimos los rangos de días para las 4 semanas del mes
    semanas_rangos = [(1, 7), (8, 14), (15, 21), (22, ultimo_dia)]
    mes_actual = hoy.month
    anio_actual = hoy.year

    for inicio, fin in semanas_rangos:
        # Calculamos el rendimiento basado en ejercicios completados en ese rango de días
        ejercicios_segmento = Ejercicio.objects.filter(
            alumno=alumno,
            fecha__year=anio_actual,
            fecha__month=mes_actual,
            fecha__day__gte=inicio,
            fecha__day__lte=fin
        )
        
        total_seg = ejercicios_segmento.count()
        completados_seg = ejercicios_segmento.filter(completado=True).count()
        
        if total_seg > 0:
            porcentaje_seg = (completados_seg / total_seg) * 100
            rendimiento.append(round(porcentaje_seg))
        else:
            rendimiento.append(0)

    # --- BARRAS DE DÍAS ---
    dias_label = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    progreso_dias = []
    for d in dias_label:
        ejs = todos_ejercicios.filter(dia_semana=d)
        t = ejs.count()
        c = ejs.filter(completado=True).count()
        progreso_dias.append({'nombre': d, 'porcentaje': int(c / t * 100) if t > 0 else 0})

    # --- RENDERIZADO ---
    return render(request, 'alumnos/dashboard.html', {
        'alumno': alumno,
        'ejercicios_hoy': ejercicios_hoy,
        'progreso_hoy': progreso_hoy,
        'progreso_dias': progreso_dias,
        'datos_distribucion': json.dumps(datos_distribucion),
        'rendimiento': json.dumps(rendimiento),
        'dia_hoy': dia_hoy_esp,
        'frase_motivadora': "¡A darle con todo! 🔥"
    })

@csrf_exempt
@login_required
def marcar_completado(request, ejercicio_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        ahora = timezone.now()
        ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id, alumno__user=request.user)
        alumno = ejercicio.alumno

        ejercicio.completado = not ejercicio.completado
        ejercicio.ultima_vez_hecho = ahora
        ejercicio.save(update_fields=['completado', 'ultima_vez_hecho'])

        ejercicios_hoy = Ejercicio.objects.filter(alumno=alumno, dia_semana=ejercicio.dia_semana)
        total_h = ejercicios_hoy.count()
        hechos_h = ejercicios_hoy.filter(completado=True).count()
        nuevo_progreso = int((hechos_h / total_h * 100)) if total_h > 0 else 0

        asistencia, _ = Asistencia.objects.get_or_create(alumno=alumno, fecha=ahora.date())
        asistencia.porcentaje_completado = nuevo_progreso
        asistencia.save(update_fields=['porcentaje_completado'])

        # Recalcular Distribución para AJAX
        realizados_hoy = ejercicios_hoy.filter(completado=True)
        if not realizados_hoy.exists():
            datos_d = [0, 0, 0]
        else:
            t_d = max(1, realizados_hoy.count())
            datos_d = [
                round((realizados_hoy.filter(tipo='FUERZA').count() / t_d) * 100),
                round((realizados_hoy.filter(tipo='AEROBICO').count() / t_d) * 100),
                round((realizados_hoy.filter(tipo='ZONA_MEDIA').count() / t_d) * 100),
            ]

        # Recalcular Rendimiento para AJAX
        mes_actual, anio_actual = ahora.month, ahora.year
        rendimiento_lista = []
        _, ultimo_dia = calendar.monthrange(anio_actual, mes_actual)
        semanas_rangos = [(1, 7), (8, 14), (15, 21), (22, ultimo_dia)]

        for inicio, fin in semanas_rangos:
            asistencias_segmento = Asistencia.objects.filter(
                alumno=alumno, fecha__year=anio_actual, fecha__month=mes_actual,
                fecha__day__gte=inicio, fecha__day__lte=fin
            )
            if asistencias_segmento.exists():
                prom_asist = asistencias_segmento.aggregate(Avg('porcentaje_completado'))['porcentaje_completado__avg'] or 0
                rendimiento_lista.append(round(prom_asist))
            else:
                rendimiento_lista.append(0)

        return JsonResponse({
            'status': 'ok',
            'completado': ejercicio.completado,
            'progreso_hoy': nuevo_progreso,
            'datos_distribucion': datos_d,
            'rendimiento': rendimiento_lista
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

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

# --- VISTAS DE ADMINISTRACIÓN ---

def control_acceso(request):
    mensaje = None
    clase_alerta = "warning"

    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        try:
            # Buscamos al alumno por su código o DNI
            alumno = Alumno.objects.get(codigo=codigo)
            
            # --- REGISTRO DE ASISTENCIA ---
            # get_or_create evita que se sumen varias asistencias si pasa el código dos veces el mismo día
            asistencia, creado = Asistencia.objects.get_or_create(
                alumno=alumno,
                fecha=timezone.now().date()
            )

            if creado:
                mensaje = f"BIENVENIDO/A {alumno.user.first_name.upper()}"
                clase_alerta = "success"
            else:
                mensaje = f"YA REGISTRASTE TU ENTRADA, {alumno.user.first_name.upper()}"
                clase_alerta = "warning"

        except Alumno.DoesNotExist:
            mensaje = "CÓDIGO NO ENCONTRADO"
            clase_alerta = "danger"

    return render(request, 'recepcion.html', {
        'mensaje': mensaje,
        'clase_alerta': clase_alerta
    })

@login_required
def gestion_gym(request):
    if not request.user.is_staff:
        return redirect('dashboard_alumno')
    
    hoy = timezone.now().date()
    alumnos_activos = Alumno.objects.filter(activo=True).select_related('user')
    alumnos_baja = Alumno.objects.filter(activo=False).select_related('user')
    
    stats_hombres, stats_mujeres = [], []
    traduccion_dias = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Lunes', 'Sunday': 'Lunes'}
    dia_hoy = traduccion_dias.get(timezone.now().strftime('%A'), 'Lunes')

    for alu in alumnos_activos:
        conteo_mes = Asistencia.objects.filter(alumno=alu, fecha__month=hoy.month).count()
        meta_mes = (alu.plan_semanal or 0) * 4
        porcentaje_asistencia = int((conteo_mes / meta_mes * 100)) if meta_mes > 0 else 0
        
        ejs_hoy = Ejercicio.objects.filter(alumno=alu, dia_semana=dia_hoy).distinct()
        t_h = ejs_hoy.count()
        progreso_hoy = int((ejs_hoy.filter(completado=True).count() / t_h * 100)) if t_h > 0 else 0

        data = {
            'alumno': alu,
            'porcentaje_asistencia': porcentaje_asistencia,
            'progreso_rutina': progreso_hoy,
            'cuota_estado': 'PAGADO' if alu.cuota_pagada else 'PENDIENTE',
            'cuota_color': '#98cf2c' if alu.cuota_pagada else '#ff4d4d',
        }
        stats_hombres.append(data) if alu.genero == 'H' else stats_mujeres.append(data)
            
    return render(request, 'alumnos/gestion.html', {
        'stats_hombres': stats_hombres, 'stats_mujeres': stats_mujeres, 'alumnos_baja': alumnos_baja
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
def agregar_ejercicio(request, alumno_id):
    if request.method == 'POST':
        alumno = get_object_or_404(Alumno, id=alumno_id)
        timer_raw = request.POST.get('timer', '')
        Ejercicio.objects.create(
            alumno=alumno,
            nombre=request.POST.get('nombre'),
            tipo=request.POST.get('tipo'),
            dia_semana=request.POST.get('dia'),
            series=request.POST.get('series') or 0,
            repeticiones=request.POST.get('reps') or "0",
            peso_sugerido=request.POST.get('peso') or 0,
            timer=timer_raw.upper().strip() if timer_raw else None
        )
        messages.success(request, "Ejercicio agregado correctamente.")
    return redirect('detalle_alumno', alumno_id=alumno_id)

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
        user = User.objects.create_user(username=codigo, first_name=nombre, last_name=apellido, password=codigo)
        Alumno.objects.create(
            user=user, codigo=codigo, genero='H' if codigo.startswith('H') else 'M',
            plan_semanal=request.POST.get('plan'), dni=request.POST.get('dni'),
            domicilio=request.POST.get('domicilio'), celular=request.POST.get('celular'),
            contacto_emergencia=request.POST.get('emergencia'), activo=True,
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
    alumno = get_object_or_404(Alumno, id=alumno_id)
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    # Buscamos los registros REALES de la recepción
    asistencias = Asistencia.objects.filter(
        alumno=alumno, 
        fecha__range=[hace_30_dias, hoy]
    ).order_by('-fecha')

    # Cálculo del porcentaje del mes (basado en 30 días)
    # Por ejemplo, si asistió 3 veces de 30 días, es 10%
    porcentaje_mes = (asistencias.count() / 30) * 100

    return render(request, 'alumnos/historial_asistencias.html', { # Agregamos 'alumnos/'
    'alumno': alumno,
    'asistencias': asistencias,
    'porcentaje_mes': porcentaje_mes
})

@login_required
def renovar_cuota(request, alumno_id):
    if not request.user.is_staff: return redirect('dashboard_alumno')
    alumno = get_object_or_404(Alumno, id=alumno_id)
    alumno.cuota_pagada = True
    alumno.fecha_pago = timezone.now().date()
    alumno.save()
    return redirect('gestion_gym')
