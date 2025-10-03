# ========== Stage 1: builder ==========
FROM python:3.9-slim AS builder
WORKDIR /smitci-app

# Env venv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Dépendances système nécessaires AU BUILD (et certaines runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libpq-dev proj-bin proj-data \
    gcc python3-dev python3-setuptools \
    libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libharfbuzz0b libfribidi0 \
    libglib2.0-0 libffi-dev libxml2 libxslt1.1 \
    libjpeg62-turbo libpng16-16 fonts-dejavu-core fonts-liberation \
    postgresql-client \
 && rm -rf /var/lib/apt/lists/*

# GDAL/PROJ env
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so \
    GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj

# Python deps
COPY requirements.txt /smitci-app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Code
COPY . /smitci-app/

# Variables nécessaires pour collectstatic (ne touche pas à la DB)
ENV DJANGO_SETTINGS_MODULE=smitci.settings \
    PYTHONUNBUFFERED=1

# Définis un STATIC_ROOT de build (doit matcher tes settings)
ENV STATIC_ROOT=/smitci-app/smitci/staticfiles
RUN mkdir -p $STATIC_ROOT

# Collecte des statics A LA BUILD (enlève le pic CPU au boot)
RUN python manage.py collectstatic --noinput

# ========== Stage 2: runtime ==========
FROM python:3.9-slim
WORKDIR /smitci-app

# Paquets RUNTIME seulement (plus léger que builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libpq-dev proj-bin proj-data \
    libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libharfbuzz0b libfribidi0 \
    libglib2.0-0 libffi-dev libxml2 libxslt1.1 \
    libjpeg62-turbo libpng16-16 fonts-dejavu-core fonts-liberation \
    postgresql-client \
 && rm -rf /var/lib/apt/lists/*

# Copie du venv et du code/statics depuis le builder
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /smitci-app /smitci-app

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000