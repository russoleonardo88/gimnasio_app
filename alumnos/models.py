from django.db import models
from django.contrib.auth.models import User


class Alumno(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.IntegerField()
    telefono = models.CharField(max_length=20)
    fecha_inscripcion = models.DateField()

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    

class Rutina(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} - {self.alumno.nombre}"

class Ejercicio(models.Model):

    TIPOS = [
        ('normal', 'Normal'),
        ('aerobico', 'Aeróbico'),
        ('abdominal', 'Abdominal'),
    ]

    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)

    dia = models.CharField(max_length=20, blank=True)

    tipo = models.CharField(max_length=20, choices=TIPOS, default='normal')

    series = models.IntegerField(null=True, blank=True)
    repeticiones = models.IntegerField(null=True, blank=True)

    tiempo = models.IntegerField(null=True, blank=True, help_text="Minutos (para aeróbico)")

    def __str__(self):
        return self.nombre