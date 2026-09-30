from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from .models import Evento, GestionLogistica

class GestionLogisticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GestionLogistica
        # Se añade 'evento' para permitir que el frontend lo envíe al crear gestiones individuales
        fields = ['id', 'evento', 'descripcion', 'plazo', 'horas_estimadas', 'completada']
    
    def validate_horas_estimadas(self, value):
        if value <= 0:
            raise serializers.ValidationError("Las horas estimadas deben ser mayores que cero.")
        return value

class EventoSerializer(serializers.ModelSerializer):
    # 'required=False' y 'allow_empty=True' permiten que el evento se cree sin plan logístico inicial
    gestiones = GestionLogisticaSerializer(many=True, required=False, allow_empty=True)

    class Meta:
        model = Evento
        # Se incluye 'limite_diario_horas' que viene del formulario principal de la interfaz
        fields = ['id', 'nombre', 'tipo', 'fecha', 'limite_diario_horas', 'creado_en', 'organizador', 'gestiones']
        read_only_fields = ['organizador'] # El backend asigna esto automáticamente por seguridad
    
    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del evento no puede estar vacío.")
        return value
    
    def validate_tipo(self, value):
        if not value.strip():
            raise serializers.ValidationError("El tipo de evento no puede estar vacío.")
        return value
    
    def create(self, validated_data):
        # Si el usuario no mandó gestiones, se asigna una lista vacía por defecto
        gestiones_data = validated_data.pop('gestiones', [])
        evento = Evento.objects.create(**validated_data)
        
        # Si se enviaron subtareas iniciales, se crean asociadas al evento; si no, se omite
        for gestion_data in gestiones_data:
            GestionLogistica.objects.create(evento=evento, **gestion_data)
        return evento


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirmation = serializers.CharField(write_only=True)
    nombre_completo = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['nombre_completo', 'email', 'password', 'password_confirmation']

    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({"password_confirmation": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        nombre_completo = validated_data.pop('nombre_completo', '')
        email = validated_data.get('email')
        
        # Usamos el correo electrónico como username automáticamente
        username = email

        # Separamos el nombre completo en first_name y last_name
        partes_nombre = nombre_completo.split(' ', 1)
        first_name = partes_nombre[0] if partes_nombre else ''
        last_name = partes_nombre[1] if len(partes_nombre) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name
        )
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=6, write_only=True)
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        try:
            # Decodificamos el ID del usuario recibido por el cliente
            uid = urlsafe_base64_decode(data['uid']).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "El enlace de recuperación es inválido."})

        # Validamos que el token criptográfico de Django sea legítimo para este usuario
        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError({"token": "El token ha expirado o es inválido."})
        
        data['user'] = user
        return data