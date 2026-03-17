from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Alumno, Ejercicio, Asistencia
from django.utils import timezone

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard_alumno')
    else:
        form = AuthenticationForm()
    return render(request, 'alumnos/login.html', {'form': form})

@login_required
def dashboard_alumno(request):
    try:
        alumno = Alumno.objects.get(user=request.user)
    except Alumno.DoesNotExist:
        return render(request, 'alumnos/dashboard.html', {'error': 'No tienes un perfil de alumno asignado.'})

    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    progreso_dias = []

    for dia in dias:
        ejercicios_dia = Ejercicio.objects.filter(alumno=alumno, dia_semana=dia)
        total = ejercicios_dia.count()
        completados = ejercicios_dia.filter(completado=True).count()
        porcentaje = (completados / total * 100) if total > 0 else 0
        
        progreso_dias.append({
            'nombre': dia,
            'porcentaje': int(porcentaje)
        })

    return render(request, 'alumnos/dashboard.html', {
        'alumno': alumno,
        'progreso_dias': progreso_dias
    })

@login_required
def mi_rutina(request):
    dia_seleccionado = request.GET.get('dia', 'Lunes')
    alumno = Alumno.objects.get(user=request.user)
    ejercicios = Ejercicio.objects.filter(alumno=alumno, dia_semana=dia_seleccionado)
    
    return render(request, 'alumnos/mi_rutina.html', {
        'ejercicios': ejercicios,
        'dia': dia_seleccionado
    })

@csrf_exempt
@login_required
def marcar_ejercicio_hecho(request, ejercicio_id):
    if request.method == 'POST':
        try:
            ejercicio = Ejercicio.objects.get(id=ejercicio_id, alumno__user=request.user)
            ejercicio.completado = not ejercicio.completado
            ejercicio.ultima_vez_hecho = timezone.now()
            ejercicio.save()
            return JsonResponse({'status': 'ok', 'completado': ejercicio.completado})
        except Ejercicio.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)

def logout_view(request):
    logout(request)
    return redirect('login')