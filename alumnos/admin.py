from django.contrib import admin
from .models import Alumno, Ejercicio, Entrenador, Asistencia

admin.site.register(Alumno)
admin.site.register(Ejercicio)
admin.site.register(Entrenador)
admin.site.register(Asistencia)