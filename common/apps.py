from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"  # type: ignore
    name = "common"
    verbose_name = "Common Models"
