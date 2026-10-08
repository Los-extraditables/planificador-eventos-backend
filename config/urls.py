# Forzar despliegue en Render
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    health, 
    hoy_view, 
    profile_view, 
    RegisterView, 
    EventoViewSet, 
    GestionLogisticaViewSet,
    password_reset_request_view,
    password_reset_confirm_view,
    limite_diario_view
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'gestiones', GestionLogisticaViewSet, basename='gestion')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Endpoints de Autenticación JWT (Login, Registro y Refresh)
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpoints de Djoser (Incluye /api/auth/users/reset_password_confirm/)
    path('api/auth/', include('djoser.urls')),
    
    # Endpoints de Recuperación de Contraseña (Lógica personalizada previa)
    path('api/password-reset/', password_reset_request_view, name='password_reset_request'),
    path('api/password-reset-confirm/', password_reset_confirm_view, name='password_reset_confirm'),
    
    # Nuevo Endpoint de Perfil de Usuario
    path('api/users/profile/', profile_view, name='user-profile'),

    # US-12: Configuración del Límite Diario de Gestión
    path('api/limite-diario/', limite_diario_view, name='limite-diario'),
    
    # Rutas existentes y nuevo endpoint de agrupación
    path('api/health/', health, name='health'), 
    path('api/hoy/', hoy_view, name='hoy-view'),
    path('api/', include(router.urls)),
    
    # Documentación Swagger / OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'), 
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), 
]