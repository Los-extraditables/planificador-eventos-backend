from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Evento, GestionLogistica
from .serializers import GestionLogisticaSerializer, EventoSerializer


@api_view(['GET'])
def health(request):
    return Response({
        'status': 'ok',
        'message': 'API funcionando correctamente'
    })

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer

class GestionLogisticaViewSet(viewsets.ModelViewSet):
    queryset = GestionLogistica.objects.all()
    serializer_class = GestionLogisticaSerializer