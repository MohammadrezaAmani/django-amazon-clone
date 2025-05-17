from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CartConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"  # type: ignore
    name = "apps.cart"
    verbose_name = _("Cart")

    def ready(self):
        import apps.cart.signals  # noqa
