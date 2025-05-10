import os

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

GDAL_LIBRARY_PATH = os.getenv('GDAL_LIBRARY_PATH', '/opt/homebrew/opt/gdal/lib/libgdal.dylib')
GEOS_LIBRARY_PATH = os.getenv('GEOS_LIBRARY_PATH', '/opt/homebrew/opt/geos/lib/libgeos_c.dylib')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'smitciv2',
        'USER': 'postgres',
        'PASSWORD': 'weddingLIFE18',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

MPI_API_KEY = os.environ.get('MPI_API_KEY', default='key')
