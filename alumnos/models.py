from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# 1. Perfil para el Entrenador (Extiende al usuario de Django)
class Entrenador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre_gym = models.CharField(max_length=100, default="Aquiles Gym")

    def __str__(self):
        return self.user.username

# 2. Perfil para el Alumno
class Alumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    entrenador = models.ForeignKey(Entrenador, on_delete=models.SET_NULL, null=True, related_name='mis_alumnos')
    fecha_inicio_rutina = models.DateField(auto_now_add=True)
    
    def dias_restantes_rutina(self):
        # Calcula cuánto falta para los 2 meses (60 días)
        vencimiento = self.fecha_inicio_rutina + timedelta(days=60)
        restante = (vencimiento - timezone.now().date()).days
        return max(0, restante)

    def __str__(self):
        return self.user.username

# 3. Modelo para los Ejercicios de la Rutina
class Ejercicio(models.Model):
    DIAS_CHOICES = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
    ]
    
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='ejercicios')
    nombre = models.CharField(max_length=100)
    dia_semana = models.CharField(max_length=15, choices=DIAS_CHOICES)
    series = models.IntegerField()
    repeticiones = models.CharField(max_length=50) # "12" o "Al fallo"
    peso_sugerido = models.FloatField(null=True, blank=True)
    
    # Campo clave para que el alumno marque progreso
    completado = models.BooleanField(default=False)
    ultima_vez_hecho = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} - {self.alumno.user.username} ({self.dia_semana})"

# 4. Registro de Asistencia Automático
class Asistencia(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    presente = models.BooleanField(default=True)

    class Meta:
        unique_together = ('alumno', 'fecha') # Evita duplicar asistencia el mismo día

    def __str__(self):
        return f"{self.alumno.user.username} - {self.fecha}"