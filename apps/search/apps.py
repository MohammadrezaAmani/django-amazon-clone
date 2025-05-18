from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"  # type: ignore
    name = "apps.search"
    verbose_name = _("Search")

    def ready(self):
        import apps.search.signals  # noqa
