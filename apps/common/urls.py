from rest_framework.routers import DefaultRouter

from .views import (  # LocationViewSet,
    ActionViewSet,
    CommentViewSet,
    ReactViewSet,
    TagViewSet,
    ViewViewSet,
)

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"actions", ActionViewSet, basename="action")
router.register(r"reacts", ReactViewSet, basename="react")
router.register(r"views", ViewViewSet, basename="view")
router.register(r"comments", CommentViewSet, basename="comment")
# router.register(r"locations", LocationViewSet, basename="location")

urlpatterns = router.urls
