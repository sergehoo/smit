FROM python:3.9-slim
LABEL authors="ogahserge"

WORKDIR /smitci-app

# Configurer l'environnement Python virtuel
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Mettre à jour pip
RUN pip install --upgrade pip

# Copier les dépendances et installer les packages système nécessaires
COPY requirements.txt /smitci-app/requirements.txt

# Installer les dépendances système pour GDAL, PostgreSQL et distutils
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libpq-dev \
    gcc \
    python3-distutils \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Définir les variables d'environnement pour GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . /smitci-app/

# Installer le client PostgreSQL pour les connexions à la base de données
RUN apt-get update && apt-get install -y postgresql-client

# Exposer le port de l'application
EXPOSE 8000

# Lancer Gunicorn avec le paramétrage adapté
CMD ["gunicorn", "smitci.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180", "--log-level=debug"]