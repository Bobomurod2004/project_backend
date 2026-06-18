from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Q

from .models import MahsulotTuri, OylikHisobot, HisobotQatori
from .serializers import (
    MahsulotTuriSerializer,
    OylikHisobotSerializer,
    OylikHisobotYaratishSerializer,
    OylikHisobotRoyxatSerializer,
    HisobotQatoriSerializer,
)
from .reports import hisobot_pdf, hisobot_excel


class MahsulotTuriViewSet(viewsets.ReadOnlyModelViewSet):
    """Mahsulot turlari — faqat o'qish (admin orqali o'zgartiriladi)."""
    queryset = MahsulotTuri.objects.all()
    serializer_class = MahsulotTuriSerializer


class OylikHisobotViewSet(viewsets.ModelViewSet):
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['yil', 'oy', 'korxona__nomi', 'yangilangan']
    ordering = ['-yil', '-oy']

    def get_queryset(self):
        qs = OylikHisobot.objects.select_related('korxona').prefetch_related(
            'qatorlar__mahsulot'
        )
        korxona_id = self.request.query_params.get('korxona')
        yil = self.request.query_params.get('yil')
        oy = self.request.query_params.get('oy')

        if korxona_id:
            qs = qs.filter(korxona_id=korxona_id)
        if yil:
            qs = qs.filter(yil=yil)
        if oy:
            qs = qs.filter(oy=oy)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return OylikHisobotYaratishSerializer
        if self.action == 'list':
            return OylikHisobotRoyxatSerializer
        return OylikHisobotSerializer

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf_yuklab_olish(self, request, pk=None):
        hisobot = self.get_object()
        buffer = hisobot_pdf(hisobot)
        fayl_nomi = f"hisobot_{hisobot.korxona.inn}_{hisobot.yil}_{hisobot.oy:02d}.pdf"
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{fayl_nomi}"'
        return response

    @action(detail=True, methods=['get'], url_path='excel')
    def excel_yuklab_olish(self, request, pk=None):
        hisobot = self.get_object()
        buffer = hisobot_excel(hisobot)
        fayl_nomi = f"hisobot_{hisobot.korxona.inn}_{hisobot.yil}_{hisobot.oy:02d}.xlsx"
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{fayl_nomi}"'
        return response


class HisobotQatoriViewSet(viewsets.ModelViewSet):
    """Bitta qatorni alohida tahrirlash uchun."""
    serializer_class = HisobotQatoriSerializer

    def get_queryset(self):
        qs = HisobotQatori.objects.select_related('mahsulot', 'hisobot__korxona')
        hisobot_id = self.request.query_params.get('hisobot')
        if hisobot_id:
            qs = qs.filter(hisobot_id=hisobot_id)
        return qs
