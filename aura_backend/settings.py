from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# SECRET_KEY signs login tokens — never fall back to a known value in production.
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'dev-only-insecure-key-do-not-use-in-production'
    else:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured('SECRET_KEY environment variable is required when DEBUG is off.')

# Comma-separated. Default covers Render + local dev; set ALLOWED_HOSTS to override.
ALLOWED_HOSTS = [h.strip() for h in os.environ.get(
    'ALLOWED_HOSTS', '.onrender.com,localhost,127.0.0.1').split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'django_celery_beat',
    'tenants',
    'users',
    'patients',
    'appointments',
    'treatments',
    'leads',
    'dashboard',
    'rest_framework_simplejwt.token_blacklist',
    'rooms',
    'clinic',
    'inventory',
    'therapist',
    'packages',
    'ai_agent',
    'payments',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tenants.middleware.TenantContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aura_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'aura_backend.wsgi.application'

# ── Database ───────────────────────────────────────────────
# ── Database ───────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Render gives postgres:// but dj_database_url needs postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if DATABASE_URL and 'postgresql' in DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600
        )
    }
elif DATABASE_URL and 'mysql' in DATABASE_URL:
    import urllib.parse
    parsed = urllib.parse.urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.mysql',
            'NAME':     parsed.path[1:],
            'USER':     parsed.username,
            'PASSWORD': parsed.password,
            'HOST':     parsed.hostname,
            'PORT':     str(parsed.port),
            'OPTIONS': {
                'ssl': {'ssl-mode': 'REQUIRED'},
                'charset': 'utf8mb4',
            }
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.mysql',
            'NAME':     'aura_clinic',
            'USER':     'root',
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST':     'localhost',
            'PORT':     '3306',
        }
    }
        
# ── Auth ───────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.User'

# Custom auth backend — allow email login
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── REST Framework ─────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Same JWT / session auth as before, plus: sets the user's clinic for the request,
        # blocks suspended clinics and users who must change their temporary password.
        'tenants.auth.TenantJWTAuthentication',
        'tenants.auth.TenantSessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Rate limits for sensitive endpoints (applied per view via throttle_scope)
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.ScopedRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {
        'auth':        '10/min',    # login, register, token refresh
        'otp_request': '5/hour',    # forgot-password
        'otp_verify':  '10/hour',   # verify-otp, reset-password
        'ai':          '30/min',    # AI chat
    },
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'AUTH_HEADER_TYPES':      ('Bearer',),
    'BLACKLIST_AFTER_ROTATION': True,  
    'ROTATE_REFRESH_TOKENS':    True,   
}

# ── CORS ───────────────────────────────────────────────────
# Set CORS_ALLOWED_ORIGINS (comma-separated) in production to restrict the API to known frontends.
# If it is not set, all origins are allowed (keeps current behaviour for local dev).
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()]
CORS_ALLOW_ALL_ORIGINS = not CORS_ALLOWED_ORIGINS
# Auth uses the Authorization header, not cookies — only allow credentials for a fixed origin list.
CORS_ALLOW_CREDENTIALS = bool(CORS_ALLOWED_ORIGINS)
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'origin',
    'x-requested-with',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# ── Static files ───────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Celery ─────────────────────────────────────────────────
CELERY_BROKER_URL    = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_TIMEZONE      = os.environ.get('TIME_ZONE', 'Asia/Kolkata')

# ── Twilio ─────────────────────────────────────────────────
TWILIO_ACCOUNT_SID   = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN    = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')

# ── Email ──────────────────────────────────────────────────
EMAIL_BACKEND     = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY  = os.environ.get('SENDGRID_API_KEY', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'info@krypsos.tech')
SENDGRID_SANDBOX_MODE_IN_DEBUG = False

# ── Cache (for OTP storage) ────────────────────────────────
# Used for OTPs and rate limiting. Set CACHE_REDIS_URL to share it across
# several server processes; otherwise an in-process cache is used.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ['CACHE_REDIS_URL'],
    } if os.environ.get('CACHE_REDIS_URL') else {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ── i18n ───────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = os.environ.get('TIME_ZONE', 'Asia/Kolkata')  # set TIME_ZONE=Europe/Madrid for the Spain clinic
USE_I18N      = True
USE_TZ        = True

DEFAULT_AUTO_FIELD   = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL   = '/api/patients/'

#------for profiles--------------------------------------------
MEDIA_URL  = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ── Production security headers ────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER        = ('HTTP_X_FORWARDED_PROTO', 'https')  # Render terminates HTTPS
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
    SECURE_HSTS_SECONDS            = int(os.environ.get('SECURE_HSTS_SECONDS', '86400'))
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    SECURE_REFERRER_POLICY         = 'same-origin'
    X_FRAME_OPTIONS                = 'DENY'

# Uploads: reject anything bigger than 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
