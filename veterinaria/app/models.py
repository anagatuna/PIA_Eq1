from django.db import models

# Create your models here.
class SERVICIO(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(max_length=250, null= True)

    def __str__(self):
        return self.nombre

class CITA_VETERINARIA(models.Model):
    nombre_dueño = models.CharField(max_length=200)
    nombre_mascota = models.CharField(max_length=100)
    especie = models.CharField(max_length=100)
    fecha_cita = models.DateTimeField()
    motivo = models.CharField(max_length=255)
    estatus = models.CharField(max_length=50)
    servicio = models.ForeignKey(SERVICIO, on_delete= models.PROTECT, null=True)

    def __str__(self):
        return self.nombre_dueño
    

