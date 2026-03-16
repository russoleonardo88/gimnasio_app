import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import Alumno, Rutina

# Vista para manejar el Login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirige a la rutina tras iniciar sesión correctamente
            return redirect('mi_rutina')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

# Vista para la rutina del alumno
@login_required
def mi_rutina(request):
    alumno = Alumno.objects.get(user=request.user)
    dia_url = request.GET.get("dia")

    if dia_url:
        hoy_es = dia_url
    else:
        hoy = datetime.datetime.today().strftime("%A")
        dias = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
        }
        hoy_es = dias.get(hoy)

    rutina_hoy = Rutina.objects.filter(alumno=alumno, nombre=hoy_es)

    ejercicios_normal = []
    ejercicios_abdominal = []
    ejercicios_aerobico = []

    for rutina in rutina_hoy:
        for ejercicio in rutina.ejercicio_set.all():
            if ejercicio.tipo == "normal":
                ejercicios_normal.append(ejercicio)
            elif ejercicio.tipo == "abdominal":
                ejercicios_abdominal.append(ejercicio)
            elif ejercicio.tipo == "aerobico":
                ejercicios_aerobico.append(ejercicio)

    return render(request, "rutina.html", {
        "rutinas": rutina_hoy,
        "dia": hoy_es,
        "ejercicios_normal": ejercicios_normal,
        "ejercicios_abdominal": ejercicios_abdominal,
        "ejercicios_aerobico": ejercicios_aerobico
    })