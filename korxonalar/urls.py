from rest_framework.routers import DefaultRouter
from .views import KorxonaViewSet

router = DefaultRouter()
router.register('korxonalar', KorxonaViewSet, basename='korxona')

urlpatterns = router.urls
