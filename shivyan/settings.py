from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

try:
    from decouple import config, Csv, UndefinedValueError
except ImportError:
    def config(key, default=None, cast=None):
        import os
        val = os.environ.get(key, default)
        if val is None and default is None:
            return None
        return cast(val) if cast and val is not None else val

    class Csv:  # noqa: PIE793
        def __call__(self, value):
            return [x.strip() for x in value.split(',') if x.strip()]

    class UndefinedValueError(Exception):
        pass

BASE_DIR = Path(__file__).resolve().parent.parent


def _public_path_url(name: str, default: str) -> str:
    """
    Public URL for static/media (same-origin path or full CDN URL).
    Ensures a trailing slash. Paths get a leading slash when not using https?://
    """
    raw = (config(name, default=default) or default).strip()
    if not raw:
        return default
    if raw.startswith(('http://', 'https://', '//')):
        return raw if raw.endswith('/') else f'{raw}/'
    if not raw.startswith('/'):
        raw = f'/{raw}'
    if not raw.endswith('/'):
        raw = f'{raw}/'
    return raw


def _content_dir(name: str, default_relative: str) -> Path:
    """
    On-disk path for staticfiles/ or user uploads. Empty env → BASE_DIR / default.
    Relative values are under BASE_DIR; absolute paths are used as-is.
    """
    val = (config(name, default='') or '').strip()
    if not val:
        return (BASE_DIR / default_relative).resolve()
    p = Path(val).expanduser()
    if p.is_absolute():
        return p
    return (BASE_DIR / p).resolve()


# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------
# ENVIRONMENT: local = development, production = live site (enforces safe defaults)
_raw_env = (config('ENVIRONMENT', default='local') or 'local').strip().lower()
if _raw_env not in ('local', 'production'):
    raise ImproperlyConfigured(
        "ENVIRONMENT must be 'local' or 'production' (case-insensitive). "
        f'Got: {_raw_env!r}'
    )
ENVIRONMENT = _raw_env
IS_PRODUCTION = ENVIRONMENT == 'production'
IS_LOCAL = ENVIRONMENT == 'local'

try:
    SECRET_KEY = config('SECRET_KEY')
except UndefinedValueError:
    SECRET_KEY = 'django-insecure-shivyan-change-xyz123'

# Production: never run with DEBUG; local: DEBUG from .env, default True
if IS_PRODUCTION:
    DEBUG = False
else:
    DEBUG = config('DEBUG', default=True, cast=bool)

# Hosts: never use * in real production; set e.g. example.com,www.example.com
ALLOWED_HOSTS = list(
    config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())
)

# e.g. https://www.example.com,https://example.com
CSRF_TRUSTED_ORIGINS = list(
    config(
        'CSRF_TRUSTED_ORIGINS',
        default='http://127.0.0.1:8000,http://localhost:8000',
        cast=Csv(),
    )
)

# -----------------------------------------------------------------------------
# Database: sqlite (default) or MySQL via PyMySQL
# -----------------------------------------------------------------------------
DB_ENGINE = config('DB_ENGINE', default='sqlite')
if DB_ENGINE == 'mysql':
    import pymysql  # noqa: WPS433

    pymysql.install_as_MySQLdb()

    # Collation: utf8mb4_unicode_ci (5.7+ / 8.0+). MySQL 8.0+ default is often utf8mb4_0900_ai_ci;
    # set MYSQL_COLLATION if the server / DB use that and you need to match.
    _mysql_collation = config('MYSQL_COLLATION', default='utf8mb4_unicode_ci').replace("'", "''")
    # utf8mb4 4-byte UTF-8: Nepali (Devanagari), symbols, emoji. Create the DB with the same
    # charset, e.g. CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    _mysql_init = (
        "SET SESSION sql_mode='STRICT_TRANS_TABLES', "
        "SESSION character_set_client='utf8mb4', "
        "SESSION character_set_results='utf8mb4', "
        "SESSION character_set_connection='utf8mb4', "
        f"SESSION collation_connection='{_mysql_collation}'"
    )

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('MYSQL_DATABASE'),
            'USER': config('MYSQL_USER'),
            'PASSWORD': config('MYSQL_PASSWORD', default=''),
            'HOST': config('MYSQL_HOST', default='127.0.0.1'),
            'PORT': config('MYSQL_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'use_unicode': True,
                'init_command': _mysql_init,
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# -----------------------------------------------------------------------------
# Application
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'ckeditor',
    'ckeditor_uploader',
    'core',
    'blog',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shivyan.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_settings',
                'core.context_processors.newsletter_flash',
                'blog.context_processors.cms_menus',
            ],
        },
    },
]

WSGI_APPLICATION = 'shivyan.wsgi.application'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = config('USE_TZ', default=True, cast=bool)

# Public URLs (e.g. /static/ or https://cdn.example.com/static/); see .env
STATIC_URL = _public_path_url('STATIC_URL', '/static/')
MEDIA_URL = _public_path_url('MEDIA_URL', '/media/')
STATIC_ROOT = _content_dir('STATIC_ROOT', 'staticfiles')
MEDIA_ROOT = _content_dir('MEDIA_ROOT', 'media')
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# -----------------------------------------------------------------------------
# Email
# -----------------------------------------------------------------------------
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@example.com')
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=25, cast=int)

# Inbox for contact form notifications (separate from SMTP login; often your team Gmail)
CONTACT_INBOX_EMAIL = config('CONTACT_INBOX_EMAIL', default='')
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# Legacy name for templates / old code; prefer CONTACT_INBOX_EMAIL in .env
if not CONTACT_INBOX_EMAIL:
    try:
        CONTACT_INBOX_EMAIL = config('CONTACT_EMAIL')
    except UndefinedValueError:
        CONTACT_INBOX_EMAIL = ''

CONTACT_EMAIL = CONTACT_INBOX_EMAIL

# Base URL for links in blog newsletter emails (unsubscribe, post). Falls back to ALLOWED_HOSTS.
NEWSLETTER_BASE_URL = config('NEWSLETTER_BASE_URL', default='').rstrip('/')
# "From" display name in subscribers' inboxes ( RFC 5322 name-addr; falls back to SiteSettings company name)
NEWSLETTER_FROM_NAME = config('NEWSLETTER_FROM_NAME', default='').strip()
# Optional: inbox for replies to newsletter messages (e.g. contact@yoursite.com)
NEWSLETTER_REPLY_TO = config('NEWSLETTER_REPLY_TO', default='').strip()
# Where “new subscriber” notifications go (defaults to CONTACT_INBOX_EMAIL)
NEWSLETTER_INBOX_EMAIL = config('NEWSLETTER_INBOX_EMAIL', default=CONTACT_INBOX_EMAIL).strip()
# Send a one-time “you’re subscribed” message when someone joins the list
NEWSLETTER_SEND_WELCOME_EMAIL = config('NEWSLETTER_SEND_WELCOME_EMAIL', default=True, cast=bool)

# -----------------------------------------------------------------------------
# HTTPS / cookie security (not applied when DEBUG=True in local)
# -----------------------------------------------------------------------------
if not DEBUG:
    _secure = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_SSL_REDIRECT = _secure
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
        'SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool
    )
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    USE_X_FORWARDED_HOST = config('USE_X_FORWARDED_HOST', default=True, cast=bool)
    if config('USE_PROXY_SSL_HEADER', default=True, cast=bool):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# -----------------------------------------------------------------------------
# CKEditor (rich text for CMS pages and blog; uploads under MEDIA)
# -----------------------------------------------------------------------------
CKEDITOR_JQUERY_URL = None
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 420,
        'width': '100%',
    },
}
CKEDITOR_RESTRICT_BY_USER = False

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_LEVEL = config('LOG_LEVEL', default='INFO' if not DEBUG else 'DEBUG')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {'level': LOG_LEVEL, 'propagate': True},
        # Prevent dev-server "hang" due to excessive autoreload/template debug logs
        'django.utils.autoreload': {'level': 'WARNING', 'propagate': False},
        'django.template': {'level': 'WARNING', 'propagate': False},
        'core': {'level': LOG_LEVEL, 'propagate': True},
        'blog': {'level': LOG_LEVEL, 'propagate': True},
    },
}
