from django.contrib import admin
from .models import Evento, GestionLogistica

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'fecha', 'organizador')
    search_fields = ('nombre',)

@admin.register(GestionLogistica)
class GestionLogisticaAdmin(admin.ModelAdmin):
    list_display = ('id', 'descripcion', 'evento', 'plazo', 'horas_estimadas', 'completada')
    list_filter = ('completada', 'plazo')