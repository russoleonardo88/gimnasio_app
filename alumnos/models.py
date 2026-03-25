from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# 1. Perfil para el Entrenador
class Entrenador(models.Model):
    # CORRECCIÓN: Se eliminó on_update que no existe en Django
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre_gym = models.CharField(max_length=100, default="Aquiles Gym")

    def __str__(self):
        return f"Entrenador: {self.user.username}"

    class Meta:
        verbose_name_plural = "Entrenadores"

# 2. Perfil para el Alumno
class Alumno(models.Model):
    GENERO_CHOICES = [
        ('H', 'Hombre'),
        ('M', 'Mujer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    entrenador = models.ForeignKey(Entrenador, on_delete=models.SET_NULL, null=True, blank=True, related_name='mis_alumnos')
    
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, default='H')
    codigo = models.CharField(max_length=10, unique=True, help_text="Ej: H0249 o M1223")
    activo = models.BooleanField(default=True, help_text="Desmarcar para dar de BAJA al socio")
    plan_semanal = models.IntegerField(default=3, help_text="Cantidad de días por semana contratados (2, 3, 4, 5)")
    
    # CUOTA
    cuota_pagada = models.BooleanField(default=False, verbose_name="¿Cuota Pagada este Mes?")
    fecha_vencimiento = models.DateField(null=True, blank=True, help_text="Fecha en que vence la cuota")
    
    # CONTACTO
    dni = models.CharField(max_length=20, blank=True, null=True, verbose_name="DNI")
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    celular = models.CharField(max_length=25, blank=True, null=True)
    contacto_emergencia = models.CharField(max_length=25, blank=True, null=True, verbose_name="Celular de Emergencia")

    # RUTINA
    fecha_inicio_rutina = models.DateField(default=timezone.now)
    
    def dias_transcurridos(self):
        diferencia = timezone.now().date() - self.fecha_inicio_rutina
        return diferencia.days

    def rutina_vencida(self):
        return self.dias_transcurridos() >= 60

    def dias_restantes_cuota(self):
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
    
    TIPO_CHOICES = [
        ('AEROBICO', '🏃‍♂️ Aeróbico'),
        ('ZONA_MEDIA', '🧘 Zona Media'),
        ('FUERZA', '💪 Fuerza'),
    ]
    
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='ejercicios')
    nombre = models.CharField(max_length=100)
    dia_semana = models.CharField(max_length=15, choices=DIAS_CHOICES)
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='FUERZA')
    
    series = models.IntegerField(default=1)
    repeticiones = models.CharField(max_length=50)
    peso_sugerido = models.FloatField(null=True, blank=True)
    
    # Este campo permitirá que tanto Aeróbico como Fuerza guarden el Timer (P1, P2, etc.)
    timer = models.CharField(max_length=10, blank=True, null=True, help_text="Ej: P1, P2, P3 o P4")

    # ESTADO
    completado = models.BooleanField(default=False)
    ultima_vez_hecho = models.DateTimeField(null=True, blank=True)
    fecha_asignacion = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['tipo', 'id']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()}) - {self.alumno.codigo}"

# 4. Registro de Asistencia
class Asistencia(models.Model):  # Corregido: Debe heredar de models.Model
    alumno = models.ForeignKey(
        'Alumno', 
        on_delete=models.CASCADE, 
        related_name='asistencias_registro'
    )
    fecha = models.DateField(auto_now_add=True)
    hora_entrada = models.TimeField(auto_now_add=True)

    class Meta:
        unique_together = ('alumno', 'fecha')  # Evita duplicar presentes el mismo día
        
    def __str__(self):
        return f"{self.alumno} - {self.fecha}"