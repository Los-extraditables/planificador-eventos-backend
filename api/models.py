from django.db import models

# Modelos base 

class Evento(models.Model):
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=100)
    fecha = models.DateField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

class GestionLogistica(models.Model):
    evento = models.ForeignKey(Evento, related_name='gestiones', on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255)
    plazo = models.DateField()
    horas_estimadas = models.DecimalField(max_digits=5, decimal_places=2)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.descripcion} - Evento : {self.evento.nombre}"
