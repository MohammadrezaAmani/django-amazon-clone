from rest_framework.routers import DefaultRouter

from .views import CouponUsageViewSet, CouponViewSet, DiscountViewSet, OrderViewSet

router = DefaultRouter()
router.register("discounts", DiscountViewSet, basename="discount")
router.register("coupons", CouponViewSet, basename="coupon")
router.register("coupon-usages", CouponUsageViewSet, basename="coupon-usage")

router.register("orders", OrderViewSet, basename="order")

urlpatterns = router.urls
