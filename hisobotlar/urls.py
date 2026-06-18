from rest_framework.routers import DefaultRouter
from .views import MahsulotTuriViewSet, OylikHisobotViewSet, HisobotQatoriViewSet

router = DefaultRouter()
router.register('mahsulot-turlari', MahsulotTuriViewSet, basename='mahsulot-turi')
router.register('hisobotlar', OylikHisobotViewSet, basename='hisobot')
router.register('hisobot-qatorlari', HisobotQatoriViewSet, basename='hisobot-qatori')

urlpatterns = router.urls
