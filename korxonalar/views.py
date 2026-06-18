from rest_framework import viewsets, filters
from .models import Korxona
from .serializers import KorxonaSerializer, KorxonaQisqaSerializer


class KorxonaViewSet(viewsets.ModelViewSet):
    queryset = Korxona.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nomi', 'inn', 'rahbar']
    ordering_fields = ['nomi', 'yaratilgan']

    def get_serializer_class(self):
        if self.action == 'list' and self.request.query_params.get('qisqa'):
            return KorxonaQisqaSerializer
        return KorxonaSerializer

    def get_queryset(self):
        qs = Korxona.objects.all()
        if self.request.query_params.get('faol'):
            qs = qs.filter(is_active=True)
        return qs
