from django.apps import AppConfig


class AuditLogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"  # type: ignore
    name = "audit_log"

    def ready(self):
        import audit_log.signals  # noqa: F401 type: ignore
