"""Local classroom demo. No accounts, database, migrations or external services."""
from pathlib import Path
import os
import secrets

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local .env file if present
_env_path = BASE_DIR / ".env"
if _env_path.is_file():
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("'").strip('"'))

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY") or secrets.token_hex(32)
DEBUG = os.environ.get("DJANGO_DEBUG", os.environ.get("DEBUG", "True")).lower() in ("true", "1", "t", "yes")
_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],.vercel.app"))
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(",") if h.strip()]
ROOT_URLCONF = "potionshop.urls"
WSGI_APPLICATION = "potionshop.wsgi.application"
INSTALLED_APPS = ["django.contrib.staticfiles", "simulator"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware",
              "django.middleware.common.CommonMiddleware",
              "django.middleware.csrf.CsrfViewMiddleware",
              "django.middleware.clickjacking.XFrameOptionsMiddleware"]
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates",
              "DIRS": [], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request"]}}]
DATABASES = {}
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
DATA_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024  # Small local-demo form payloads.
