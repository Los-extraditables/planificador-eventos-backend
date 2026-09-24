from rest_framework import serializers
from .models import Evento, GestionLogistica

class GestionLogisticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GestionLogistica
        fields = ['id', 'descripcion', 'plazo', 'horas_estimadas', 'completada']
    
    def validate_horas_estimadas(self, value):
        if value <= 0:
            raise serializers.ValidationError("Las horas estimadas deben ser mayores que cero.")
        return value

class EventoSerializer(serializers.ModelSerializer):
    gestiones = GestionLogisticaSerializer(many=True, required=False)

    class Meta:
        model = Evento
        fields = ['nombre', 'tipo', 'fecha', 'creado_en', 'gestiones']
    
    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del evento no puede estar vacío.")
        return value
    
    def validate_tipo(self, value):
        if not value.strip():
            raise serializers.ValidationError("El tipo de evento no puede estar vacío.")
        return value
    
    def create(self, validated_data):
        gestiones_data = validated_data.pop('gestiones', [])
        evento = Evento.objects.create(**validated_data)
        for gestion_data in gestiones_data:
            GestionLogistica.objects.create(evento=evento, **gestion_data)
        return evento