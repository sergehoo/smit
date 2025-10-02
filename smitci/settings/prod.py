import os
import sys

from .base import *

DEBUG = True

# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', default='localhost').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',  # Correct engine for GIS support
        'NAME': os.environ.get('DATABASE_NAME'),
        'USER': os.environ.get('DATABASE_USER'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
        'HOST': os.environ.get('DATABASE_HOST'),
        'PORT': os.environ.get('DATABASE_PORT'),
    }
}


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MPI_API_KEY = os.environ.get('MPI_API_KEY', default='key')

META_WA_API_VERSION = os.environ.get('META_WA_API_VERSION')  # ou "v21.0" selon ta version
META_WA_PHONE_NUMBER_ID = os.environ.get('META_WA_PHONE_NUMBER_ID')  # ID du numéro WhatsApp (Cloud API)
META_WA_ACCESS_TOKEN = os.environ.get('META_WA_ACCESS_TOKEN ')  # Permanent token (ou app token régénéré)
META_WA_BASE_URL = os.environ.get(' META_WA_BASE_URL')


# Configuration de base
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5  # nombre max d'échecs avant blocage
AXES_COOLOFF_TIME = timedelta(hours=1)  # durée avant déblocage auto
AXES_LOCK_OUT_AT_FAILURE = True
AXES_RESET_ON_SUCCESS = True  # reset échecs après login réussi
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address", "user_agent"]
AXES_VERBOSE = True  # Pour logguer dans la console
AXES_FAILURE_LOG_PER_USER_LIMIT = 100  # Historique d’échecs par user
AXES_REVERSE_PROXY_HEADER = "HTTP_X_FORWARDED_FOR"

# ✅ Nouveau style
AXES_USE_X_FORWARDED_FOR = True

AXES_PROXY_DEPTH = 1  # profondeur des proxies (ajuste si tu as plusieurs reverse proxies)
# Permet de garder la session même après fermeture du navigateur
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


ALLOWED_HOSTS = ["smitci.com", "www.smitci.com", "localhost", "127.0.0.1"]

CSRF_TRUSTED_ORIGINS = [
    "https://smitci.com",
    "https://www.smitci.com",
]

CORS_ALLOWED_ORIGINS = [
    "https://smitci.com",
    "https://www.smitci.com",
]
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
# Cookies
SESSION_COOKIE_DOMAIN = ".smitci.com"
CSRF_COOKIE_DOMAIN = ".smitci.com"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
SECURE_SSL_REDIRECT = True