import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# 🔐 SECURITY / ENV SETTINGS
# ==============================
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-expense-tracker")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = (
    os.getenv("ALLOWED_HOSTS").split(",")
    if os.getenv("ALLOWED_HOSTS")
    else []
)

# ==============================
# 📦 INSTALLED APPS
# ==============================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "expenses",
]

# ==============================
# ⚙️ MIDDLEWARE (ORDER MATTERS)
# ==============================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",   # ✅ FIXED POSITION
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ==============================
# 🌐 URL CONFIG
# ==============================
ROOT_URLCONF = "expense_tracker.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "expense_tracker.wsgi.application"
ASGI_APPLICATION = "expense_tracker.asgi.application"

# ==============================
# 🗄️ DATABASE (Render PostgreSQL)
# ==============================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # Local fallback
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ==============================
# 🔐 AUTH
# ==============================
AUTH_PASSWORD_VALIDATORS = []

# ==============================
# 🌍 INTERNATIONALIZATION
# ==============================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ==============================
# 📁 STATIC FILES (WhiteNoise)
# ==============================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ==============================
# 🔗 CORS SETTINGS
# ==============================
CORS_ALLOWED_ORIGINS = (
    os.getenv("CORS_ALLOWED_ORIGINS").split(",")
    if os.getenv("CORS_ALLOWED_ORIGINS")
    else []
)

# 🚨 TEMPORARY (for debugging only)
# Uncomment if CORS still fails
# CORS_ALLOW_ALL_ORIGINS = True

# ==============================
# 🔐 CSRF SETTINGS
# ==============================
CSRF_TRUSTED_ORIGINS = (
    os.getenv("CSRF_TRUSTED_ORIGINS").split(",")
    if os.getenv("CSRF_TRUSTED_ORIGINS")
    else []
)

# ==============================
# 🔒 SECURITY FLAGS
# ==============================
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True") == "True"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True") == "True"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"

# ==============================
# 🔧 DEFAULT FIELD
# ==============================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"