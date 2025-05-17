import os
from datetime import timedelta
from pathlib import Path

from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-96heki=*w5p#^#!6x#k#urqnn=43(a06uyt(#dq_^he6&#l0e!",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://localhost,https://localhost,https://*.bank.test,https://yourdomain.com",
).split(",")
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "guardian",
    "channels",
    "django_ratelimit",
    "mptt",
    "django_countries",
    "encrypted_model_fields",
    "drf_spectacular",
    "corsheaders",
    "azbankgateways",
    "django_celery_beat",
    "django_celery_results",
    "debug_toolbar",
    "silk",
    "accounts",
    "notifications",
    "audit_log",
    "common",
    "payment",
    "feedback",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "audit_log.middleware.AuditLogMiddleware",
    "silk.middleware.SilkyMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fa"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True
LANGUAGES = [
    ("fa", _("Persian")),
    ("en", _("English")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"
GUARDIAN_RAISE_EXCEPTION = True
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Django Starter Kit",
    "DESCRIPTION": "🚀 A production-ready API with modular components",
    "VERSION": "1.0.2",
    "SERVE_INCLUDE_SCHEMA": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "tryItOutEnabled": True,
        "defaultModelsExpandDepth": -1,
        "defaultModelExpandDepth": 2,
        "docExpansion": "none",
        "filter": True,
        "displayRequestDuration": True,
        "syntaxHighlight": {"activate": True},
        "tagsSorter": "alpha",
        "operationsSorter": "method",
    },
    "SECURITY": [
        {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT Authorization using the Bearer scheme. Example: `Authorization: Bearer <token>`",
            }
        }
    ],
    "ENUM_NAME_OVERRIDES": {
        "ErrorEnum": {
            "invalid_credentials": "🔑 Invalid username or password",
            "account_disabled": "⛔ User account is disabled",
            "invalid_token": "❌ Token is invalid or expired",
            "blacklisted_token": "🚫 Token has been blacklisted",
        }
    },
    "POSTPROCESSING_HOOKS": ["drf_spectacular.hooks.postprocess_schema_enums"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.environ.get("JWT_SECRET_KEY", "your-secret-key"),
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_DB = os.environ.get("REDIS_DB", 0)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "your-email@gmail.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "your-email-password")
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_HOST_USER", "your-email@gmail.com")


CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Tehran"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"


SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
        environment="production" if not DEBUG else "development",
    )


INTERNAL_IPS = ["127.0.0.1"]


SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True


def SILKY_PERMISSIONS(user):
    return user.is_superuser


SILKY_META = True
SILKY_INTERCEPT_PERCENT = 100 if DEBUG else 10

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "app.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "sentry": {
            "level": "ERROR",
            "class": "sentry_sdk.integrations.logging.SentryHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["file", "console", "sentry"],
            "level": "INFO",
            "propagate": True,
        },
        "django": {
            "handlers": ["file", "console", "sentry"],
            "level": "INFO",
            "propagate": False,
        },
        "payment": {
            "handlers": ["file", "console", "sentry"],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery": {
            "handlers": ["file", "console", "sentry"],
            "level": "INFO",
            "propagate": False,
        },
        "feedback": {
            "handlers": ["file", "console", "sentry"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:8000,https://yourdomain.com,https://*.bank.test",
).split(",")
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "x-csrftoken",
    "x-requested-with",
]

RATELIMIT_ENABLE = True
RATELIMIT_CACHE = "default"
RATELIMIT_KEY = "user_or_ip"
RATELIMIT_RATE = "100/m"

FIELD_ENCRYPTION_KEY = os.environ.get(
    "FIELD_ENCRYPTION_KEY", "q7lJgCoBmfTBzEa-3uWZIxWwl9p-zvX7VXXHHBvwBUQ="
)

AZ_IRANIAN_BANK_GATEWAYS = {
    "GATEWAYS": {
        "BMI": {
            "MERCHANT_CODE": os.environ.get("BMI_MERCHANT_CODE", ""),
            "TERMINAL_CODE": os.environ.get("BMI_TERMINAL_CODE", ""),
            "SECRET_KEY": os.environ.get("BMI_SECRET_KEY", ""),
        },
        "SEP": {
            "MERCHANT_CODE": os.environ.get("SEP_MERCHANT_CODE", ""),
            "TERMINAL_CODE": os.environ.get("SEP_TERMINAL_CODE", ""),
        },
        "ZARINPAL": {
            "MERCHANT_CODE": os.environ.get("ZARINPAL_MERCHANT_CODE", ""),
            "SANDBOX": int(os.environ.get("ZARINPAL_SANDBOX", 0)),
        },
        "IDPAY": {
            "MERCHANT_CODE": os.environ.get("IDPAY_MERCHANT_CODE", ""),
            "METHOD": "POST",
            "X_SANDBOX": int(os.environ.get("IDPAY_X_SANDBOX", 0)),
        },
        "ZIBAL": {
            "MERCHANT_CODE": os.environ.get("ZIBAL_MERCHANT_CODE", ""),
        },
        "BAHAMTA": {
            "MERCHANT_CODE": os.environ.get("BAHAMTA_MERCHANT_CODE", ""),
        },
        "MELLAT": {
            "TERMINAL_CODE": os.environ.get("MELLAT_TERMINAL_CODE", ""),
            "USERNAME": os.environ.get("MELLAT_USERNAME", ""),
            "PASSWORD": os.environ.get("MELLAT_PASSWORD", ""),
        },
        "PAYV1": {
            "MERCHANT_CODE": os.environ.get("PAYV1_MERCHANT_CODE", ""),
            "X_SANDBOX": int(os.environ.get("PAYV1_X_SANDBOX", 0)),
        },
    },
    "IS_SAMPLE_FORM_ENABLE": DEBUG,
    "DEFAULT": "SEP",
    "CURRENCY": "IRR",
    "TRACKING_CODE_QUERY_PARAM": "tc",
    "TRACKING_CODE_LENGTH": 16,
    "SETTING_VALUE_READER_CLASS": "azbankgateways.readers.DefaultReader",
    "BANK_PRIORITIES": [
        "SEP",
        "BMI",
        "ZARINPAL",
        "IDPAY",
        "ZIBAL",
        "BAHAMTA",
        "MELLAT",
        "PAYV1",
    ],
    "IS_SAFE_GET_GATEWAY_PAYMENT": True,
    "CUSTOM_APP": "payment",
    "CALLBACK_NAMESPACE": "payment:callback",
}
