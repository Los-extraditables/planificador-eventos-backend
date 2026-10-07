from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# US-12: Perfil de usuario para almacenar configuraciones personalizadas como el límite diario
class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    limite_diario_horas = models.DecimalField(max_digits=5, decimal_places=2, default=6.00)

    def __str__(self):
        return f"Perfil de {self.usuario.username} - Límite: {self.limite_diario_horas}h"

# Crear o guardar automáticamente el perfil al crear un usuario
@receiver(post_save, sender=User)
def crear_o_guardar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)
    else:
        if hasattr(instance, 'perfil'):
            instance.perfil.save()

# Modelos base con aislamiento por organizador

class Evento(models.Model):
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=100)
    fecha = models.DateField()
    limite_diario_horas = models.DecimalField(max_digits=5, decimal_places=2, default=6.0) # Campo agregado según la interfaz de creación
    creado_en = models.DateTimeField(auto_now_add=True)
    
    # Campo agregado para vincular el evento estrictamente al usuario logueado
    organizador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventos', null=True, blank=True)

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