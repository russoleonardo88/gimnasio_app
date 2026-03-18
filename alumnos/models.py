from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# 1. Perfil para el Entrenador
class Entrenador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre_gym = models.CharField(max_length=100, default="Aquiles Gym")

    def __str__(self):
        return f"Entrenador: {self.user.username}"

# 2. Perfil para el Alumno
class Alumno(models.Model):
    GENERO_CHOICES = [
        ('H', 'Hombre'),
        ('M', 'Mujer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    entrenador = models.ForeignKey(Entrenador, on_delete=models.SET_NULL, null=True, related_name='mis_alumnos')
    
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, default='H')
    codigo = models.CharField(max_length=10, unique=True, help_text="Ej: H0249 o M1223")
    activo = models.BooleanField(default=True, help_text="Desmarcar para dar de BAJA al socio")
    plan_semanal = models.IntegerField(default=3, help_text="Cantidad de días por semana contratados (2, 3, 4, 5)")
    
    # --- NUEVO CAMPO PARA PAGOS ---
    fecha_vencimiento = models.DateField(null=True, blank=True, help_text="Fecha en que vence la cuota")

    fecha_inicio_rutina = models.DateField(default=timezone.now)
    
    def dias_transcurridos(self):
        """Calcula cuántos días lleva con la rutina actual"""
        diferencia = timezone.now().date() - self.fecha_inicio_rutina
        return diferencia.days

    def rutina_vencida(self):
        """Devuelve True si pasaron más de 60 días"""
        return self.dias_transcurridos() >= 60

    def dias_restantes_plan(self):
        """Calcula cuántos días le quedan de cuota"""
        if self.fecha_vencimiento:
            delta = self.fecha_vencimiento - timezone.now().date()
            return delta.days
        return None

    def __str__(self):
        return f"{self.codigo} - {self.user.first_name} {self.user.last_name}"

# 3. Modelo para los Ejercicios
class Ejercicio(models.Model):
    DIAS_CHOICES = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
    ]
    
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='ejercicios')
    nombre = models.CharField(max_length=100)
    dia_semana = models.CharField(max_length=15, choices=DIAS_CHOICES)
    series = models.IntegerField()
    repeticiones = models.CharField(max_length=50) 
    peso_sugerido = models.FloatField(null=True, blank=True)
    completado = models.BooleanField(default=False)
    ultima_vez_hecho = models.DateTimeField(null=True, blank=True)
    fecha_asignacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.alumno.codigo} ({self.dia_semana})"

# 4. Registro de Asistencia
class Asistencia(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField(default=timezone.now)
    hora_entrada = models.TimeField(auto_now_add=True)
    porcentaje_completado = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('alumno', 'fecha')

    def __str__(self):
        return f"{self.alumno.codigo} - {self.fecha}"