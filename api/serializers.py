from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from .models import Evento, GestionLogistica, PerfilUsuario

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = ['limite_diario_horas']

    def validate_limite_diario_horas(self, value):
        if value <= 0:
            raise serializers.ValidationError("El límite diario de horas debe ser mayor a 0.")
        if value > 24:
            raise serializers.ValidationError("El límite diario de horas no puede superar las 24 horas.")
        return value

class GestionLogisticaSerializer(serializers.ModelSerializer):
    # 'required=False' y 'allow_null=True' permiten que las gestiones anidadas 
    # se validen correctamente antes de que el evento exista en la base de datos.
    evento = serializers.PrimaryKeyRelatedField(
        queryset=Evento.objects.all(), 
        required=False, 
        allow_null=True
    )

    class Meta:
        model = GestionLogistica
        fields = ['id', 'evento', 'descripcion', 'plazo', 'horas_estimadas', 'completada']
    
    def validate_horas_estimadas(self, value):
        if value <= 0:
            raise serializers.ValidationError("Las horas estimadas deben ser mayores que cero.")
        return value

class EventoSerializer(serializers.ModelSerializer):
    gestiones = GestionLogisticaSerializer(many=True, required=False, allow_empty=True)

    class Meta:
        model = Evento
        fields = ['id', 'nombre', 'tipo', 'fecha', 'limite_diario_horas', 'creado_en', 'organizador', 'gestiones']
        read_only_fields = ['organizador']
    
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
            # Evitamos conflictos si el JSON trae 'evento' explícitamente
            gestion_data.pop('evento', None)
            
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
        
        username = email

        # Guarda el nombre completo entero en first_name sin dividirlo
        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data['password'],
            first_name=nombre_completo,
            last_name=''
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
            uid = urlsafe_base64_decode(data['uid']).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "El enlace de recuperación es inválido."})

        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError({"token": "El token ha expirado o es inválido."})
        
        data['user'] = user
        return data