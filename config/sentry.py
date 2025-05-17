import os

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from audit_log.utils import log_sentry_error


def init_sentry():
    dsn = os.environ.get("SENTRY_DSN", "")
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[DjangoIntegration(), CeleryIntegration()],
            traces_sample_rate=1.0,
            send_default_pii=True,
            environment=(
                "production"
                if not os.environ.get("DJANGO_DEBUG", "True") == "True"
                else "development"
            ),
            before_send=lambda event, hint: log_sentry_error(
                event.get("event_id"), metadata=event
            )
            or event,
        )
