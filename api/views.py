import os
import requests
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import viewsets, generics, status, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer
from .models import Evento, GestionLogistica, PerfilUsuario
from .serializers import (
    GestionLogisticaSerializer, 
    EventoSerializer, 
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PerfilUsuarioSerializer
)


@api_view(['GET'])
def health(request):
    return Response({
        'status': 'ok',
        'message': 'API funcionando correctamente'
    })


class RegisterView(generics.CreateAPIView):
    """
    Endpoint para el registro de nuevos usuarios desde el formulario de Evora.
    Permite acceso libre (AllowAny).
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


@extend_schema(
    request=PasswordResetRequestSerializer,
    responses={200: {"detail": "Si el correo existe, se han enviado las instrucciones."}}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """
    Recibe el email, genera el token y envía el correo corporativo de Evora usando la API HTTP de Brevo.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = User.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(str(user.pk).encode())
                
                # Obtener la URL del frontend desde las variables de entorno (con fallback a localhost si no está definida)
                frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
                reset_link = f"{frontend_url}/reset-password?uid={uid}&token={token}"
                
                html_message = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Restablecer contraseña - Evora</title>
                </head>
                <body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f3f4f6; padding: 40px 0;">
                        <tr>
                            <td align="center">
                                <table role="presentation" style="width: 100%; max-width: 540px; border-collapse: collapse; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);">
                                    <tr>
                                        <td style="padding: 45px 40px 35px 40px; text-align: center; background: linear-gradient(135deg, #2e1065 0%, #4c1d95 50%, #6d28d9 100%); border-top-left-radius: 16px; border-top-right-radius: 16px;">
                                            <h2 style="color: #ffffff; font-size: 22px; font-weight: 600; margin: 0;">Restablecer contraseña</h2>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 40px 40px 35px 40px;">
                                            <p style="color: #334155; font-size: 16px; line-height: 1.5; margin-top: 0;">Hola,</p>
                                            <p style="color: #475569; font-size: 15px; line-height: 1.6;">Recibimos una solicitud para actualizar la contraseña de tu cuenta en Evora. Haz clic en el botón inferior:</p>
                                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 30px 0;">
                                                <tr>
                                                    <td align="center">
                                                        <a href="{reset_link}" target="_blank" style="background-color: #2e1065; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 600; display: inline-block; font-size: 15px;">Cambiar mi contraseña</a>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
                
                # Configuración de credenciales de Brevo desde variables de entorno
                brevo_api_key = os.environ.get('BREVO_API_KEY')
                sender_email = os.environ.get('BREVO_SENDER_EMAIL')
                
                url = "https://api.brevo.com/v3/smtp/email"
                headers = {
                    "accept": "application/json",
                    "api-key": brevo_api_key,
                    "content-type": "application/json"
                }
                payload = {
                    "sender": {
                        "name": "Evora",
                        "email": sender_email
                    },
                    "to": [
                        {
                            "email": user.email
                        }
                    ],
                    "subject": "Restablece tu contraseña - Evora",
                    "htmlContent": html_message
                }
                
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 201:
                    print("Correo enviado exitosamente con Brevo a:", user.email)
                else:
                    print("Error de Brevo:", response.text)
                
        except Exception as e:
            print(f"Error al enviar correo de recuperación con Brevo: {e}")
            
        return Response({"detail": "Si el correo existe, se han enviado las instrucciones."}, status=200)
    return Response(serializer.errors, status=400)


@extend_schema(
    request=PasswordResetConfirmSerializer,
    responses={200: {"detail": "Contraseña actualizada exitosamente."}}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Contraseña actualizada exitosamente."}, status=200)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "limite_diario_horas": perfil.limite_diario_horas
    }, status=200)


# ==========================================
# US-12: Endpoints para límite diario por usuario
# ==========================================
@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def limite_diario_view(request):
    """
    US-12: Permite consultar (GET) y actualizar (PUT/PATCH) el límite máximo
    de horas de gestión diarias del usuario autenticado (por defecto 6.0 horas).
    """
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)

    if request.method == 'GET':
        serializer = PerfilUsuarioSerializer(perfil)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = PerfilUsuarioSerializer(perfil, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "mensaje": "Límite diario de gestión actualizado correctamente.",
                "limite_diario_horas": serializer.data['limite_diario_horas']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    parameters=[
        OpenApiParameter('evento', description='ID del evento para filtrar', required=False, type=OpenApiTypes.INT),
        OpenApiParameter('completada', description='Filtrar por completada (true/false)', required=False, type=OpenApiTypes.STR),
    ]
)
@api_view(['GET'])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def hoy_view(request):
    hoy_fecha = timezone.now().date()
    usuario_actual = request.user

    gestiones = GestionLogistica.objects.filter(
        evento__organizador=usuario_actual
    )

    evento_id = request.GET.get('evento')
    if evento_id:
        gestiones = gestiones.filter(evento_id=evento_id)

    completada_param = request.GET.get('completada')
    if completada_param is not None:
        if completada_param.lower() in ['true', '1']:
            gestiones = gestiones.filter(completada=True)
        elif completada_param.lower() in ['false', '0']:
            gestiones = gestiones.filter(completada=False)

    gestiones = gestiones.order_by('plazo', 'horas_estimadas')

    vencidas = []
    para_hoy = []
    proximas = []

    for gestion in gestiones:
        serializer = GestionLogisticaSerializer(gestion)
        if gestion.plazo < hoy_fecha and not gestion.completada:
            vencidas.append(serializer.data)
        elif gestion.plazo == hoy_fecha:
            para_hoy.append(serializer.data)
        elif gestion.plazo > hoy_fecha:
            proximas.append(serializer.data)

    return Response({
        "vencidas": vencidas,
        "para_hoy": para_hoy,
        "proximas": proximas
    }, status=200)


class EventoViewSet(viewsets.ModelViewSet):
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, JWTAuthentication]

    def get_queryset(self):
        return Evento.objects.filter(organizador=self.request.user)

    def perform_create(self, serializer):
        serializer.save(organizador=self.request.user)


class GestionLogisticaViewSet(viewsets.ModelViewSet):
    """
    US-06 & US-07: Endpoints de reprogramación (PUT/PATCH) con detección automática
    de sobrecarga de horas según el límite diario del usuario.
    """
    serializer_class = GestionLogisticaSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, JWTAuthentication]

    def get_queryset(self):
        return GestionLogistica.objects.filter(
            evento__organizador=self.request.user
        ).order_by('plazo', 'horas_estimadas')

    def perform_create(self, serializer):
        evento = serializer.validated_data.get('evento')
        if evento.organizador != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No puedes agregar gestiones a un evento que no te pertenece.")
        serializer.save()

    def update(self, request, *args, **kwargs):
        """
        US-06 & US-07: Permite reprogramar la fecha (plazo) u otros campos.
        Antes de guardar, valida si acumula más horas que el límite diario del usuario.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        nuevo_plazo = serializer.validated_data.get('plazo', instance.plazo)
        nuevas_horas_raw = serializer.validated_data.get('horas_estimadas', instance.horas_estimadas)
        nuevas_horas = Decimal(str(nuevas_horas_raw))

        # US-07: Validación de límite de horas diarias en el servidor
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
        limite_diario = Decimal(str(perfil.limite_diario_horas))

        # Calcular horas ocupadas ese día excluyendo la gestión actual
        horas_acumuladas_query = GestionLogistica.objects.filter(
            evento__organizador=request.user,
            plazo=nuevo_plazo
        ).exclude(pk=instance.pk).aggregate(total=Sum('horas_estimadas'))['total']

        horas_acumuladas = Decimal(str(horas_acumuladas_query or '0.0'))
        total_proyectado = horas_acumuladas + nuevas_horas

        # Si supera el límite diario y la petición no incluye confirmación explícita
        force_save = request.data.get('force', False)
        if total_proyectado > limite_diario and not force_save:
            exceso = total_proyectado - limite_diario
            horas_disponibles = max(Decimal('0.0'), limite_diario - horas_acumuladas)

            return Response({
                "conflicto": True,
                "mensaje": f"La reprogramación excede tu límite diario de horas ({limite_diario}h).",
                "detalles": {
                    "fecha_objetivo": str(nuevo_plazo),
                    "limite_diario": float(limite_diario),
                    "horas_acumuladas_previas": float(horas_acumuladas),
                    "horas_tarea": float(nuevas_horas),
                    "total_horas_proyectado": float(total_proyectado),
                    "exceso_horas": float(exceso),
                    "horas_disponibles_en_fecha": float(horas_disponibles)
                },
                "opciones_resolucion": [
                    {
                        "codigo": "REDUCIR_TIEMPO",
                        "descripcion": f"Reducir las horas de esta tarea a {horas_disponibles}h para encajar en el día.",
                        "tiempo_sugerido": float(horas_disponibles)
                    },
                    {
                        "codigo": "MOVER_FECHA",
                        "descripcion": "Mover la tarea a un día disponible."
                    }
                ]
            }, status=status.HTTP_409_CONFLICT)

        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # US-08: Servicio para resolución atómica de conflictos
    @extend_schema(
        request=inline_serializer(
            name='ResolverConflictoPayload',
            fields={
                'opcion': serializers.CharField(default='REDUCIR_TIEMPO'),
                'nueva_fecha': serializers.DateField(required=False),
                'nuevas_horas': serializers.FloatField(default=2.5, required=False)
            }
        )
    )
    @action(detail=True, methods=['post'], url_path='resolver-conflicto')
    @transaction.atomic
    def resolver_conflicto(self, request, pk=None):
        """
        US-08: Resuelve un conflicto de forma atómica.
        Payload esperado:
        - opcion: "MOVER_FECHA" | "REDUCIR_TIEMPO"
        - nueva_fecha: "YYYY-MM-DD" (si opcion es MOVER_FECHA)
        - nuevas_horas: N (si opcion es REDUCIR_TIEMPO)
        """
        gestion = self.get_object()
        opcion = request.data.get('opcion')

        if opcion == 'MOVER_FECHA':
            nueva_fecha = request.data.get('nueva_fecha')
            if not nueva_fecha:
                return Response({"error": "Debe proporcionar 'nueva_fecha' para mover la tarea."}, status=status.HTTP_400_BAD_REQUEST)
            
            gestion.plazo = nueva_fecha
            gestion.save()
            return Response({
                "mensaje": "Conflicto resuelto: Fecha reprogramada con éxito.",
                "gestion": GestionLogisticaSerializer(gestion).data
            }, status=status.HTTP_200_OK)

        elif opcion == 'REDUCIR_TIEMPO':
            nuevas_horas = request.data.get('nuevas_horas')
            if nuevas_horas is None or Decimal(str(nuevas_horas)) <= 0:
                return Response({"error": "Debe proporcionar 'nuevas_horas' mayores a 0."}, status=status.HTTP_400_BAD_REQUEST)
            
            gestion.horas_estimadas = Decimal(str(nuevas_horas))
            gestion.save()
            return Response({
                "mensaje": "Conflicto resuelto: Horas reducidas con éxito.",
                "gestion": GestionLogisticaSerializer(gestion).data
            }, status=status.HTTP_200_OK)

        else:
            return Response({
                "error": "Opción no válida. Use 'MOVER_FECHA' o 'REDUCIR_TIEMPO'."
            }, status=status.HTTP_400_BAD_REQUEST)