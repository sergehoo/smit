FROM python:3.9-slim
LABEL authors="ogahserge"

WORKDIR /smitci-app

# ---- venv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# ---- dépendances système (runtime + build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # GeoDjango / Postgres
    gdal-bin libgdal-dev libpq-dev proj-bin proj-data \
    # Build tools pour pip
    gcc python3-dev python3-setuptools \
    # WeasyPrint (runtime)
    libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libharfbuzz0b libfribidi0 \
    libglib2.0-0 libffi-dev libxml2 libxslt1.1 \
    # Codecs/Images + polices
    libjpeg62-turbo libpng16-16 fonts-dejavu-core fonts-liberation \
    # Outils utiles
    postgresql-client \
 && rm -rf /var/lib/apt/lists/*

# ---- GDAL/PROJ env
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so \
    GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj

# ---- pip + deps projet
RUN pip install --upgrade pip
COPY requirements.txt /smitci-app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ⚠️ (Optionnel) torch & co → à mettre plutôt dans l'image worker
# RUN pip install --no-cache-dir \
#     "torch==2.2.2" "torchvision==0.17.2" \
#     torchxrayvision==0.0.32 pydicom scikit-image numpy
# # (Optionnel) pré-téléchargement de poids — je déconseille en image web
# ENV TORCH_HOME=/opt/torch-cache
# RUN mkdir -p ${TORCH_HOME} && chmod -R 777 ${TORCH_HOME}
# RUN python - <<'PY'
# print("SKIP pretrained weights in web image.")
# PY

# ---- code
COPY . /smitci-app/

# ---- entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000
# ❌ Retirer CMD pour éviter les conflits avec `command:` dans compose
# CMD ["gunicorn", "smitci.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180", "--log-level=debug"]



#FROM python:3.9-slim
#LABEL authors="ogahserge"
#
#WORKDIR /smitci-app
#
## ---- venv
#ENV VIRTUAL_ENV=/opt/venv
#RUN python3 -m venv $VIRTUAL_ENV
#ENV PATH="$VIRTUAL_ENV/bin:$PATH"
#
## ---- dépendances système (runtime + build)
## On installe d'abord tout (build + runtime) puis on purge les libs de build
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    # Postgres / GDAL
#    gdal-bin libgdal-dev libpq-dev \
#    # Build tools pour pip (purgera ensuite)
#    gcc python3-dev python3-setuptools \
#    # WeasyPrint (runtime)
#    libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
#    libgdk-pixbuf-2.0-0 libharfbuzz0b libfribidi0 \
#    libglib2.0-0 libffi-dev libxml2 libxslt1.1 \
#    # Codecs/Images + polices
#    libjpeg62-turbo libpng16-16 fonts-dejavu-core fonts-liberation \
# && rm -rf /var/lib/apt/lists/*
#
#
## GDAL env
#ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
#ENV C_INCLUDE_PATH=/usr/include/gdal
#ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
#
#ENV TORCH_HOME=/opt/torch-cache
#RUN python - <<'PY'
#import torch
#from torchvision.models import resnet50, ResNet50_Weights
#from torchvision.models.detection import fasterrcnn_resnet50_fpn, FasterRCNN_ResNet50_FPN_Weights
#
## Télécharge les poids
#resnet50(weights=ResNet50_Weights.DEFAULT)
#fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)
#PY
#
#RUN pip install --no-cache-dir torchxrayvision==0.0.32 pydicom scikit-image numpy
## pip
#RUN pip install --upgrade pip
#
## ---- deps Python
#COPY requirements.txt /smitci-app/requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt
#
## ---- code
#COPY . /smitci-app/
#
## Client psql (utile pour mgts/backup)
#RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
# && rm -rf /var/lib/apt/lists/*
#
#
## (optionnel) purge des paquets de build pour réduire l’image
## RUN apt-get purge -y gcc python3-dev libgdal-dev libpq-dev libffi-dev && apt-get autoremove -y
#
#EXPOSE 8000
#CMD ["gunicorn", "smitci.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180", "--log-level=debug"]