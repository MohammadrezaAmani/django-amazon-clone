from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("notifications/", include("notifications.urls")),
    path("logs/", include("audit_log.urls")),
    path("payment/", include("payment.urls")),
    path("c/", include("common.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("feedback/", include("feedback.urls")),
    path("silk/", include("silk.urls", namespace="silk")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
