from rest_framework.routers import DefaultRouter

from .views import SalesReportViewSet, UserActivityViewSet

router = DefaultRouter()
router.register("activities", UserActivityViewSet, basename="activity")
router.register("reports", SalesReportViewSet, basename="report")

urlpatterns = router.urls
