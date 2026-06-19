from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone

from .models import MahsulotTuri, OylikHisobot, HisobotQatori
from .serializers import (
    MahsulotTuriSerializer,
    OylikHisobotSerializer,
    OylikHisobotYaratishSerializer,
    OylikHisobotRoyxatSerializer,
    HisobotQatoriSerializer,
)
from .reports import hisobot_pdf, hisobot_excel, oylik_svod_data, svodlar_data


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

    @action(detail=True, methods=['get'], url_path='svod')
    def svod(self, request, pk=None):
        """Korxonaning shu yildagi oy-ma-oy svodi (umumiy ko'rinish)."""
        hisobot = self.get_object()
        return Response(oylik_svod_data(hisobot.korxona, hisobot.yil))

    @action(detail=False, methods=['get'], url_path='svodlar')
    def svodlar(self, request):
        """Oylar kesimida, har oy ichida korxonalar bo'yicha svod."""
        yil_raw = request.query_params.get('yil') or timezone.localdate().year
        oy_raw = request.query_params.get('oy')
        korxona_raw = request.query_params.get('korxona')

        try:
            yil = int(yil_raw)
        except (TypeError, ValueError):
            return Response(
                {'detail': "Yil noto'g'ri kiritilgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        oy = None
        if oy_raw:
            try:
                oy = int(oy_raw)
            except (TypeError, ValueError):
                return Response(
                    {'detail': "Oy noto'g'ri kiritilgan."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if oy < 1 or oy > 12:
                return Response(
                    {'detail': "Oy 1 dan 12 gacha bo'lishi kerak."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        korxona_id = None
        if korxona_raw:
            try:
                korxona_id = int(korxona_raw)
            except (TypeError, ValueError):
                return Response(
                    {'detail': "Korxona noto'g'ri kiritilgan."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(svodlar_data(yil, korxona_id=korxona_id, oy=oy))

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
