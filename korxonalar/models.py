# flake8: noqa
from django.db import models


class Korxona(models.Model):
    nomi = models.CharField(max_length=255, verbose_name="Korxona nomi")
    inn = models.CharField(max_length=20, unique=True, verbose_name="INN")
    manzil = models.CharField(max_length=500, blank=True, verbose_name="Manzil")
    rahbar = models.CharField(max_length=255, blank=True, verbose_name="Rahbar")
    telefon = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="Email")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    yaratilgan = models.DateTimeField(auto_now_add=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Korxona"
        verbose_name_plural = "Korxonalar"
        ordering = ['nomi']

    def __str__(self):
        return f"{self.nomi} ({self.inn})"
