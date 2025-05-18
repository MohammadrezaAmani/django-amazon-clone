from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"  # type: ignore
    name = "apps.orders"
    verbose_name = _("Orders")

    def ready(self):
        import apps.orders.signals  # noqa
