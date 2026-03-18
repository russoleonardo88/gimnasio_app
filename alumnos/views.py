# --- BUSCÁ ESTAS FUNCIONES Y REEMPLAZALAS ---

@login_required
def mi_rutina(request):
    traduccion_dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Lunes'
    }
    dia_default = traduccion_dias.get(timezone.now().strftime('%A'), 'Lunes')
    dia_seleccionado = request.GET.get('dia', dia_default)
    alumno = get_object_or_404(Alumno, user=request.user)
    
    # IMPORTANTE: Asegurate de que el filtro use dia_semana si así se llama en tu modelo
    ejercicios = Ejercicio.objects.filter(alumno=alumno, dia_semana=dia_seleccionado)
    
    hoy = timezone.now().date()
    for ej in ejercicios:
        if ej.ultima_vez_hecho and ej.ultima_vez_hecho.date() < hoy:
            ej.completado = False
            ej.save()

    return render(request, 'mi_rutina.html', {'ejercicios': ejercicios, 'dia': dia_seleccionado, 'alumno': alumno})

@login_required
def agregar_ejercicio(request, alumno_id):
    if request.method == 'POST':
        alumno = get_object_or_404(Alumno, id=alumno_id)
        
        # Capturamos los datos del formulario
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo') # Recibe 'FUERZA', 'AEROBICO' o 'ZONA_MEDIA'
        dia = request.POST.get('dia')
        series = request.POST.get('series') or 0
        reps = request.POST.get('reps')
        peso = request.POST.get('peso')
        
        # Limpiamos el peso por si viene vacío
        if not peso or peso == "":
            peso = 0

        Ejercicio.objects.create(
            alumno=alumno,
            nombre=nombre,
            tipo=tipo,
            dia_semana=dia, # Verificá que en tu models.py se llame dia_semana
            series=series,
            repeticiones=reps,
            peso_sugerido=peso
        )
        # CORRECCIÓN: Redirigir al detalle usando el ID numérico
        return redirect('detalle_alumno', alumno_id=alumno.id)
    
    return redirect('gestion_gym')