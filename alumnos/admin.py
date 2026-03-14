from django.contrib import admin
from .models import Alumno, Rutina, Ejercicio


class EjercicioInline(admin.TabularInline):
    model = Ejercicio
    extra = 1


class RutinaAdmin(admin.ModelAdmin):
    inlines = [EjercicioInline]


admin.site.register(Alumno)
admin.site.register(Rutina, RutinaAdmin)