# flake8: noqa
from rest_framework import serializers
from .models import MahsulotTuri, OylikHisobot, HisobotQatori


class MahsulotTuriSerializer(serializers.ModelSerializer):
    class Meta:
        model = MahsulotTuri
        fields = '__all__'


class HisobotQatoriSerializer(serializers.ModelSerializer):
    mahsulot_nomi = serializers.CharField(source='mahsulot.nomi', read_only=True)
    mahsulot_tartib = serializers.IntegerField(source='mahsulot.tartib_raqam', read_only=True)
    mahsulot_meta = serializers.SerializerMethodField()

    class Meta:
        model = HisobotQatori
        fields = [
            'id', 'hisobot', 'mahsulot', 'mahsulot_nomi', 'mahsulot_tartib', 'mahsulot_meta',
            # Yil boshiga qoldiq
            'yil_boshi_hajmi', 'yil_boshi_absolyut',
            # Qabul qilingan
            'qabul_hajmi',
            # Ishlab chiqarishga sarflangan
            'sarflangan_hajmi',
            # Ishlab chiqarish
            'ishlab_hajmi', 'ishlab_absolyut',
            # Realizatsiya
            'realizatsiya_hajmi', 'realizatsiya_absolyut', 'realizatsiya_summasi',
            # Eksport
            'eksport_hajmi', 'eksport_absolyut', 'eksport_summasi',
            # Yo'qotishlar
            'yoqotish_hajmi',
            # O'z ehtiyoji
            'oz_ehtiyoj_hajmi',
            # Oy oxiriga qoldiq
            'oy_oxiri_hajmi', 'oy_oxiri_absolyut',
        ]
        read_only_fields = [
            'mahsulot_nomi', 'mahsulot_tartib', 'mahsulot_meta',
            'oy_oxiri_hajmi', 'oy_oxiri_absolyut',
        ]

    def validate(self, data):
        from decimal import Decimal

        def get(field):
            # patch uchun: yangi qiymat bo'lmasa instance'dan olish
            if field in data:
                return data[field] or Decimal('0')
            if self.instance:
                return getattr(self.instance, field) or Decimal('0')
            return Decimal('0')

        real_haj = get('realizatsiya_hajmi')
        real_abs = get('realizatsiya_absolyut')
        real_sum = get('realizatsiya_summasi')
        eksp_haj = get('eksport_hajmi')
        eksp_abs = get('eksport_absolyut')
        eksp_sum = get('eksport_summasi')

        errors = {}
        if eksp_haj > real_haj:
            errors['eksport_hajmi'] = (
                f'Eksport hajmi ({eksp_haj}) realizatsiyadan '
                f'({real_haj}) oshib ketdi.'
            )
        if eksp_abs > real_abs:
            errors['eksport_absolyut'] = (
                f'Eksport absolyut spirt ({eksp_abs}) realizatsiyadan '
                f'({real_abs}) oshib ketdi.'
            )
        if eksp_sum > real_sum:
            errors['eksport_summasi'] = (
                f'Eksport summasi ({eksp_sum}) realizatsiya summasidan '
                f'({real_sum}) oshib ketdi.'
            )

        # "x" belgilangan ustunlar — bu mahsulot uchun to'ldirilmaydi, qabul qilinmaydi
        mahsulot = data.get('mahsulot') or (self.instance.mahsulot if self.instance else None)
        if mahsulot is not None:
            FLAG_FIELDS = {
                'qabul_mavjud': ['qabul_hajmi'],
                'sarflangan_mavjud': ['sarflangan_hajmi'],
                'ishlab_chiqarish_mavjud': ['ishlab_hajmi', 'ishlab_absolyut'],
                'realizatsiya_mavjud': ['realizatsiya_hajmi', 'realizatsiya_absolyut', 'realizatsiya_summasi'],
                'eksport_mavjud': ['eksport_hajmi', 'eksport_absolyut', 'eksport_summasi'],
            }
            for flag, fields in FLAG_FIELDS.items():
                if getattr(mahsulot, flag):
                    continue
                for f in fields:
                    if f in data and data[f] is not None and data[f] != Decimal('0'):
                        errors[f] = "Bu ustun ushbu mahsulot uchun to'ldirilmaydi."

        if errors:
            raise serializers.ValidationError(errors)
        return data

    def get_mahsulot_meta(self, obj):
        m = obj.mahsulot
        return {
            'qabul_mavjud': m.qabul_mavjud,
            'sarflangan_mavjud': m.sarflangan_mavjud,
            'ishlab_chiqarish_mavjud': m.ishlab_chiqarish_mavjud,
            'realizatsiya_mavjud': m.realizatsiya_mavjud,
            'eksport_mavjud': m.eksport_mavjud,
        }


class OylikHisobotSerializer(serializers.ModelSerializer):
    korxona_nomi = serializers.CharField(source='korxona.nomi', read_only=True)
    oy_nomi = serializers.CharField(read_only=True)
    qatorlar = HisobotQatoriSerializer(many=True, read_only=True)

    class Meta:
        model = OylikHisobot
        fields = [
            'id', 'korxona', 'korxona_nomi',
            'yil', 'oy', 'oy_nomi',
            'yaratilgan', 'yangilangan',
            'qatorlar',
        ]
        read_only_fields = ['yaratilgan', 'yangilangan', 'korxona_nomi', 'oy_nomi']


class OylikHisobotYaratishSerializer(serializers.ModelSerializer):
    """Hisobot yaratish — qatorlar avtomatik 11 ta mahsulot bilan yaratiladi."""
    class Meta:
        model = OylikHisobot
        fields = ['id', 'korxona', 'yil', 'oy']

    def create(self, validated_data):
        from .models import MahsulotTuri
        hisobot = OylikHisobot.objects.create(**validated_data)
        mahsulotlar = MahsulotTuri.objects.all().order_by('tartib_raqam')
        for mahsulot in mahsulotlar:
            q = HisobotQatori(hisobot=hisobot, mahsulot=mahsulot)
            q.save()
        return hisobot


class OylikHisobotRoyxatSerializer(serializers.ModelSerializer):
    """Ro'yxat ko'rinishi — qatorlarsiz, tezroq."""
    korxona_nomi = serializers.CharField(source='korxona.nomi', read_only=True)
    oy_nomi = serializers.CharField(read_only=True)

    class Meta:
        model = OylikHisobot
        fields = ['id', 'korxona', 'korxona_nomi', 'yil', 'oy', 'oy_nomi', 'yangilangan']
