import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Local apps
    "apps.users",
    "apps.hospitals",
    "apps.bookings",
    "apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database (PostgreSQL) ---
# NOTE: Using plain lat/lng float fields for now (see apps/hospitals/models.py).
# Upgrade ENGINE to "django.contrib.gis.db.backends.postgis" + add "django.contrib.gis"
# to INSTALLED_APPS later (Week 4, Day 22) once you need real geospatial queries
# for nearest-hospital emergency matching. Requires GDAL/GEOS installed on your machine.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "medbeds"),
        "USER": os.environ.get("DB_USER", "admin"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "admin"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# --- Custom user model ---
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

# Identity document uploads (Day 18) — files are encrypted before being written here (see
# apps/users/encryption.py), so even direct filesystem access wouldn't expose readable IDs.
# Never served via Django's normal static/media URL serving — always through the
# access-controlled download view in apps/users/views.py.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "booking_create": "10/hour",   # anti-fraud: rate-limit booking spam
        "emergency_booking": "5/hour",  # separate, slightly looser limit for genuine emergencies
        "otp_request": "5/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# --- CORS (React dev server) ---
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")

# --- Third-party service keys (set via env in production) ---
SMS_API_KEY = os.environ.get("SMS_API_KEY", "")
PAYMENT_GATEWAY_KEY = os.environ.get("PAYMENT_GATEWAY_KEY", "")
PAYMENT_GATEWAY_SECRET = os.environ.get("PAYMENT_GATEWAY_SECRET", "")

# Razorpay — leave blank to run in dev-stub mode (see apps/bookings/payments.py).
# Get free test keys at https://dashboard.razorpay.com/app/keys when ready.
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

# Identity document encryption (Day 18). Leave blank in dev — a key gets derived from
# SECRET_KEY automatically (see apps/users/encryption.py). MUST be set explicitly in
# production via a real secret (e.g. Fernet.generate_key()), never left to the dev fallback.
ID_DOCUMENT_ENCRYPTION_KEY = os.environ.get("ID_DOCUMENT_ENCRYPTION_KEY", "")

# --- Celery (background jobs: SLA timers, no-show detection, notifications) ---
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# --- Security hardening (Day 29) ---
# All of these are conditional on DEBUG=False so local development over plain HTTP still
# works — enabling SECURE_SSL_REDIRECT etc. in dev would break `python manage.py runserver`
# on localhost, which doesn't serve HTTPS. In production (DEBUG=False), these all activate
# automatically with zero extra configuration needed beyond setting DJANGO_DEBUG=False.
if not DEBUG:
    SECURE_SSL_REDIRECT = True          # force HTTP -> HTTPS
    SESSION_COOKIE_SECURE = True        # cookies only sent over HTTPS
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000      # 1 year — tells browsers to always use HTTPS for this domain
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True  # stops browsers from guessing content-type in ways that enable XSS
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"            # prevents this site being embedded in an iframe (clickjacking)
    SECURE_REFERRER_POLICY = "same-origin"
