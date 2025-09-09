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
