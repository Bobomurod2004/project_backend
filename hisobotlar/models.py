# flake8: noqa
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from korxonalar.models import Korxona


class MahsulotTuri(models.Model):
    """
    Spirtli ichimlik mahsulot turlari (jadval satrlari).
    qabul_mavjud, sarflangan_mavjud, ishlab_mavjud — "x" belgilangan
    ustunlar ushbu mahsulot uchun to'ldirilmaydi.
    """
    tartib_raqam = models.PositiveSmallIntegerField(unique=True, verbose_name="T/p")
    nomi = models.CharField(max_length=200, verbose_name="Mahsulot nomi")

    # Qaysi ustunlar bu mahsulot uchun mavjud (False = "x", to'ldirilmaydi)
    qabul_mavjud = models.BooleanField(
        default=True,
        verbose_name="Qabul qilingan ustuni mavjud"
    )
    sarflangan_mavjud = models.BooleanField(
        default=True,
        verbose_name="Ishlab chiqarishga sarflangan ustuni mavjud"
    )
    ishlab_chiqarish_mavjud = models.BooleanField(
        default=True,
        verbose_name="Ishlab chiqarish ustuni mavjud"
    )
    realizatsiya_mavjud = models.BooleanField(
        default=True,
        verbose_name="Realizatsiya ustuni mavjud"
    )
    eksport_mavjud = models.BooleanField(
        default=True,
        verbose_name="Eksport ustuni mavjud"
    )

    class Meta:
        verbose_name = "Mahsulot turi"
        verbose_name_plural = "Mahsulot turlari"
        ordering = ['tartib_raqam']

    def __str__(self):
        return f"{self.tartib_raqam}. {self.nomi}"


class OylikHisobot(models.Model):
    """
    Bir korxonaning bir oylik hisoboti (jadvalning bir varag'i).
    """
    OY_CHOICES = [
        (1, 'Yanvar'), (2, 'Fevral'), (3, 'Mart'),
        (4, 'Aprel'), (5, 'May'), (6, 'Iyun'),
        (7, 'Iyul'), (8, 'Avgust'), (9, 'Sentabr'),
        (10, 'Oktabr'), (11, 'Noyabr'), (12, 'Dekabr'),
    ]

    korxona = models.ForeignKey(
        Korxona,
        on_delete=models.CASCADE,
        related_name='hisobotlar',
        verbose_name="Korxona"
    )
    yil = models.PositiveSmallIntegerField(
        verbose_name="Yil",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )
    oy = models.PositiveSmallIntegerField(
        choices=OY_CHOICES,
        verbose_name="Oy",
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    yaratilgan = models.DateTimeField(auto_now_add=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Oylik hisobot"
        verbose_name_plural = "Oylik hisobotlar"
        unique_together = ['korxona', 'yil', 'oy']
        ordering = ['-yil', '-oy']

    def __str__(self):
        return f"{self.korxona.nomi} — {self.yil} / {self.get_oy_display()}"

    @property
    def oy_nomi(self):
        return self.get_oy_display()


class HisobotQatori(models.Model):
    """
    Oylik hisobotning har bir mahsulot uchun bir qatori.
    Barcha miqdorlar dal (dekalitr) hisobida.
    Summalar so'm hisobida.
    null=True — "x" belgilangan (tegishli bo'lmagan) ustunlar uchun.
    """
    D = {'max_digits': 15, 'decimal_places': 3, 'null': True, 'blank': True}
    S = {'max_digits': 18, 'decimal_places': 2, 'null': True, 'blank': True}

    hisobot = models.ForeignKey(
        OylikHisobot,
        on_delete=models.CASCADE,
        related_name='qatorlar',
        verbose_name="Hisobot"
    )
    mahsulot = models.ForeignKey(
        MahsulotTuri,
        on_delete=models.PROTECT,
        related_name='qatorlar',
        verbose_name="Mahsulot turi"
    )

    # --- Yil boshiga qoldiq ---
    yil_boshi_hajmi = models.DecimalField(**D, verbose_name="Yil boshi qoldiq (hajmi, dal)")
    yil_boshi_absolyut = models.DecimalField(**D, verbose_name="Yil boshi qoldiq (absolyut spirt, dal)")

    # --- Qabul qilingan (products 7-11 uchun; 1-6 uchun x) ---
    qabul_hajmi = models.DecimalField(**D, verbose_name="Qabul qilingan (dal)")

    # --- Ishlab chiqarishga sarflangan (products 7-11; 1-6 uchun x) ---
    sarflangan_hajmi = models.DecimalField(**D, verbose_name="Ishlab chiqarishga sarflangan (dal)")

    # --- Ishlab chiqarish (products 1-6, 8-11; 7 uchun x) ---
    ishlab_hajmi = models.DecimalField(**D, verbose_name="Ishlab chiqarish (hajmi, dal)")
    ishlab_absolyut = models.DecimalField(**D, verbose_name="Ishlab chiqarish (absolyut spirt, dal)")

    # --- Realizatsiya ---
    realizatsiya_hajmi = models.DecimalField(**D, verbose_name="Realizatsiya (hajmi, dal)")
    realizatsiya_absolyut = models.DecimalField(**D, verbose_name="Realizatsiya (absolyut spirt, dal)")
    realizatsiya_summasi = models.DecimalField(**S, verbose_name="Realizatsiya (summasi, so'm)")

    # --- Shundan, eksportga ---
    eksport_hajmi    = models.DecimalField(**D, verbose_name="Eksport (hajmi, dal)")
    eksport_absolyut = models.DecimalField(**D, verbose_name="Eksport (absolyut spirt, dal)")
    eksport_summasi  = models.DecimalField(**S, verbose_name="Eksport (summasi, so'm)")

    # --- Yo'qotishlar ---
    yoqotish_hajmi = models.DecimalField(**D, verbose_name="Yo'qotishlar (dal)")

    # --- O'z ehtiyoji uchun ---
    oz_ehtiyoj_hajmi = models.DecimalField(**D, verbose_name="O'z ehtiyoji uchun (dal)")

    # --- Oy oxiriga qoldiq (avtomatik hisoblanadi) ---
    oy_oxiri_hajmi = models.DecimalField(**D, verbose_name="Oy oxiri qoldiq (hajmi, dal)")
    oy_oxiri_absolyut = models.DecimalField(**D, verbose_name="Oy oxiri qoldiq (absolyut spirt, dal)")

    class Meta:
        verbose_name = "Hisobot qatori"
        verbose_name_plural = "Hisobot qatorlari"
        unique_together = ['hisobot', 'mahsulot']
        ordering = ['mahsulot__tartib_raqam']

    def __str__(self):
        return f"{self.hisobot} — {self.mahsulot.nomi}"

    def _hisobla_oy_oxiri(self):
        from decimal import Decimal
        Z = Decimal('0')
        m = self.mahsulot

        def s(v, mavjud=True):
            if not mavjud:
                return Z
            return v if v is not None else Z

        self.oy_oxiri_hajmi = (
            s(self.yil_boshi_hajmi)
            + s(self.qabul_hajmi,       m.qabul_mavjud)
            + s(self.ishlab_hajmi,      m.ishlab_chiqarish_mavjud)
            - s(self.sarflangan_hajmi,  m.sarflangan_mavjud)
            - s(self.realizatsiya_hajmi, m.realizatsiya_mavjud)
            - s(self.yoqotish_hajmi)
            - s(self.oz_ehtiyoj_hajmi)
        )

        self.oy_oxiri_absolyut = (
            s(self.yil_boshi_absolyut)
            + s(self.ishlab_absolyut,       m.ishlab_chiqarish_mavjud)
            - s(self.realizatsiya_absolyut,  m.realizatsiya_mavjud)
        )

    def save(self, *args, **kwargs):
        self._hisobla_oy_oxiri()
        super().save(*args, **kwargs)
