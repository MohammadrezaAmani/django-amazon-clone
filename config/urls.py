from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin URLs
    path("admin/", admin.site.urls),
    # Application URLs
    path("accounts/", include("apps.accounts.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("logs/", include("apps.audit_log.urls")),
    path("payment/", include("apps.payment.urls")),
    path("c/", include("apps.common.urls")),
    path("feedback/", include("apps.feedback.urls")),
    path("/", include("apps.orders.urls")),
    # API Documentation URLs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Profiling URLs
    path("silk/", include("silk.urls", namespace="silk")),
]

# Debug-specific URLs
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
