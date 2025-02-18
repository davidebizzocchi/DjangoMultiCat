"""
Django settings for app project.

Generated by 'django-admin startproject' using Django 5.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
from decouple import config
import os
from django.contrib.messages import constants as messages
import sentry_sdk
from app.pre_utils import get_version_from_file
    
ENVIRONMENT_TYPE = config("ENVIRONMENT_TYPE", default="none")

# Sentry init
sentry_sdk.init(
    dsn=config("SENTRY_DNS"),
    environment=ENVIRONMENT_TYPE,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=config("SENTRY_traces_sample_rate", cast=float, default=1.0),
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=config("SENTRY_profiles_sample_rate", cast=float, default=1.0),
    send_default_pii=True,
    release=get_version_from_file()
)

LLM_PROVIDER_API_URL = config("LLM_PROVIDER_API_URL", "")
LLM_PROVIDER_API_KEY = config("LLM_PROVIDER_API_KEY", "")
LLM_MODEL_TEXT_ID = config("LLM_MODEL_TEXT_ID", "")
LLM_MODEL_AUDIO_TRANSCRIPTION_ID = config("LLM_MODEL_AUDIO_TRANSCRIPTION_ID", "")
# LLM_MODEL_AUDIO_SPEAK_ID = config("LLM_MODEL_AUDIO_ID", "gtts")  # if not given use gtts (Google Translate’s text-to-speech API)
LLM_MODEL_AUDIO_SPEAK_ID = "gtts"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")]
)

# Per testare le pagine di errore anche con DEBUG = True
HANDLER404 = 'app.views.handler404'
HANDLER403 = 'app.views.handler403'
HANDLER500 = 'app.views.handler500'

# CRSF and CORS
CRSFsites = config(
    "CSRF_TRUSTED_ORIGINS", cast=lambda v: [s.strip() for s in v.split(",")]
)
CSRF_TRUSTED_ORIGINS = CRSFsites
CSRF_ALLOWED_ORIGINS = CRSFsites
CORS_ORIGINS_WHITELIST = CRSFsites

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    # CheshireCat app
    "cheshire_cat",
    # your app
    "common",
    "users",
    "chat",
    "library",
    "user_upload",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": config("SQL_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": config("SQL_DATABASE", default=os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": config("SQL_USER", default="user"),
        "PASSWORD": config("SQL_PASSWORD", default="password"),
        "HOST": config("SQL_HOST", default="localhost"),
        "PORT": config("SQL_PORT", default=5432, cast=int),
    }
}

# Email configuration
# EMAIL_BACKEND= "django.core.mail.backends.console.EmailBackend"

AUTHENTICATION_BACKENDS = [
    'users.auth.UsernameAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',  # mantieni anche il backend predefinito se necessario
]

# Login/Logout redirect URLs
LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'users:login'
LOGOUT_REDIRECT_URL = 'home'

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=25, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", cast=bool)
# EMAIL_FILE_PATH = BASE_DIR / 'emails'
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")
# Imposta il timeout di connessione per il server Django (in secondi)
CONN_MAX_AGE = 0  # default is 0 https://docs.djangoproject.com/en/5.0/ref/databases/


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "it-IT"
TIME_ZONE = "CET"
USE_I18N = True
USE_TZ = True
USE_L10N = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    # "/var/www/static/",
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


MESSAGE_TAGS = {
    messages.DEBUG: "alert-secondary",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

UPLOADS_ROOT = MEDIA_ROOT / "uploads"