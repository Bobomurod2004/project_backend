from rest_framework import serializers
from .models import Korxona


class KorxonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Korxona
        fields = '__all__'
        read_only_fields = ['yaratilgan', 'yangilangan']


class KorxonaQisqaSerializer(serializers.ModelSerializer):
    """Faqat id va nomi — dropdown/select uchun."""
    class Meta:
        model = Korxona
        fields = ['id', 'nomi', 'inn']
