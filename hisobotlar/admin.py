from django.contrib import admin
from .models import MahsulotTuri, OylikHisobot, HisobotQatori


@admin.register(MahsulotTuri)
class MahsulotTuriAdmin(admin.ModelAdmin):
    list_display = [
        'tartib_raqam', 'nomi',
        'qabul_mavjud', 'sarflangan_mavjud',
        'ishlab_chiqarish_mavjud', 'realizatsiya_mavjud', 'eksport_mavjud'
    ]
    ordering = ['tartib_raqam']


class HisobotQatoriInline(admin.TabularInline):
    model = HisobotQatori
    extra = 0
    fields = [
        'mahsulot',
        'yil_boshi_hajmi', 'yil_boshi_absolyut',
        'qabul_hajmi', 'sarflangan_hajmi',
        'ishlab_hajmi', 'ishlab_absolyut',
        'realizatsiya_hajmi', 'realizatsiya_absolyut', 'realizatsiya_summasi',
        'eksport_absolyut', 'eksport_summasi',
        'yoqotish_hajmi', 'oz_ehtiyoj_hajmi',
        'oy_oxiri_hajmi', 'oy_oxiri_absolyut',
    ]


@admin.register(OylikHisobot)
class OylikHisobotAdmin(admin.ModelAdmin):
    list_display = ['korxona', 'yil', 'oy', 'yaratilgan']
    list_filter = ['yil', 'oy', 'korxona']
    search_fields = ['korxona__nomi']
    inlines = [HisobotQatoriInline]


@admin.register(HisobotQatori)
class HisobotQatoriAdmin(admin.ModelAdmin):
    list_display = ['hisobot', 'mahsulot', 'oy_oxiri_hajmi', 'oy_oxiri_absolyut']
    list_filter = ['hisobot__yil', 'hisobot__oy', 'mahsulot']
    search_fields = ['hisobot__korxona__nomi', 'mahsulot__nomi']
