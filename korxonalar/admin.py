from django.contrib import admin
from .models import Korxona


@admin.register(Korxona)
class KorxonaAdmin(admin.ModelAdmin):
    list_display = ['nomi', 'inn', 'rahbar', 'telefon', 'is_active', 'yaratilgan']
    list_filter = ['is_active']
    search_fields = ['nomi', 'inn', 'rahbar']
