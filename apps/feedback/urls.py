from rest_framework.routers import DefaultRouter

from .views import FeedbackViewSet

router = DefaultRouter()
router.register("", FeedbackViewSet, basename="feedback")

urlpatterns = router.urls
