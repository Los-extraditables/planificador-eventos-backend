import os
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMultiAlternatives  # <-- Importante para enviar correos HTML con Gmail
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from .models import Evento, GestionLogistica
from .serializers import (
    GestionLogisticaSerializer, 
    EventoSerializer, 
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
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
    Recibe el email, genera el token y envía el correo corporativo de Evora usando Gmail SMTP de Django.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = User.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(str(user.pk).encode())
                
                # Enlace que consumirá tu frontend (React/Vite)
                reset_link = f"http://localhost:5173/reset-password?uid={uid}&token={token}"
                
                # Plantilla HTML corporativa de Evora
                html_message = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Restablecer contraseña - Evora</title>
                </head>
                <body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
                    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f3f4f6; padding: 40px 0;">
                        <tr>
                            <td align="center">
                                <table role="presentation" style="width: 100%; max-width: 540px; border-collapse: collapse; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.08); overflow: hidden;">
                                    
                                    <!-- Encabezado con degradado -->
                                    <tr>
                                        <td style="padding: 45px 40px 35px 40px; text-align: center; background: linear-gradient(135deg, #2e1065 0%, #4c1d95 50%, #6d28d9 100%); border-top-left-radius: 16px; border-top-right-radius: 16px;">
                                            <div style="display: inline-block; background: rgba(255, 255, 255, 0.15); padding: 8px 18px; border-radius: 8px; margin-bottom: 15px;">
                                                <span style="color: #ffffff; font-size: 18px; font-weight: 700; letter-spacing: 0.5px;">Evora</span>
                                            </div>
                                            <h2 style="color: #ffffff; font-size: 22px; font-weight: 600; margin: 0; letter-spacing: 0.3px;">Restablecer contraseña</h2>
                                        </td>
                                    </tr>
                                    
                                    <!-- Contenido de la tarjeta blanca -->
                                    <tr>
                                        <td style="padding: 40px 40px 35px 40px;">
                                            <p style="color: #334155; font-size: 16px; line-height: 1.5; margin-top: 0; margin-bottom: 16px;">
                                                Hola,
                                            </p>
                                            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin-top: 0; margin-bottom: 28px;">
                                                Recibimos una solicitud para actualizar la contraseña de tu cuenta en Evora. Haz clic en el botón inferior para continuar con el proceso:
                                            </p>
                                            
                                            <!-- Botón de acción principal -->
                                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                                                <tr>
                                                    <td align="center">
                                                        <a href="{reset_link}" target="_blank" style="background-color: #2e1065; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 600; display: inline-block; font-size: 15px; box-shadow: 0 4px 12px rgba(46, 16, 101, 0.25);">Cambiar mi contraseña</a>
                                                    </td>
                                                </tr>
                                            </table>
                                            
                                            <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin-bottom: 8px;">
                                                Si tienes problemas con el botón, copia y pega el siguiente enlace en tu navegador web:
                                            </p>
                                            <p style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; font-size: 12px; color: #6d28d9; word-break: break-all; margin-top: 0; margin-bottom: 28px;">
                                                <a href="{reset_link}" target="_blank" style="color: #6d28d9; text-decoration: underline;">{reset_link}</a>
                                            </p>
                                            
                                            <div style="border-top: 1px solid #f1f5f9; padding-top: 20px; margin-top: 10px;">
                                                <p style="color: #94a3b8; font-size: 12px; line-height: 1.5; margin: 0;">
                                                    Si no solicitaste este cambio, puedes ignorar este mensaje con tranquilidad; tu cuenta seguirá estando protegida.
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                    
                                    <!-- Pie de página -->
                                    <tr>
                                        <td style="background-color: #f8fafc; padding: 20px 40px; text-align: center; border-top: 1px solid #f1f5f9;">
                                            <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                                                Plataforma de Gestión Evora &bull; 2026
                                            </p>
                                        </td>
                                    </tr>
                                    
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
                
                # Texto plano alternativo por si el cliente de correo no soporta HTML
                subject = "Restablece tu contraseña - Evora"
                text_content = f"Hola, recibe este mensaje para restablecer tu contraseña en Evora. Copia y pega el siguiente enlace: {reset_link}"
                
                # Envío usando el sistema SMTP de Django (toma los datos del .env automáticamente)
                email_message = EmailMultiAlternatives(subject, text_content, None, [user.email])
                email_message.attach_alternative(html_message, "text/html")
                email_message.send()
                
        except Exception as e:
            print(f"Error al enviar correo de recuperación con Gmail: {e}")
            
        return Response({"detail": "Si el correo existe, se han enviado las instrucciones."}, status=200)
    return Response(serializer.errors, status=400)


@extend_schema(
    request=PasswordResetConfirmSerializer,
    responses={200: {"detail": "Contraseña actualizada exitosamente."}}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """
    Recibe el uid, el token y la nueva contraseña para actualizarla en la base de datos.
    """
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
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name
    }, status=200)


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
    serializer_class = GestionLogisticaSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, JWTAuthentication]

    def get_queryset(self):
        return GestionLogistica.objects.filter(
            evento__organizador=self.request.user
        ).order_by('plazo', 'horas_estimadas')