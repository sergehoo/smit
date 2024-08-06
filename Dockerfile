FROM python:3.9-slim
LABEL authors="ogahserge"

ENV DJANGO_SETTINGS_MODULE=smitci.settings

WORKDIR /smit-app

COPY requirements.txt /smit-app/requirements.txt

RUN pip install -r requirements.txt

COPY . /smit-app/

#RUN python3 manage.py makemigrations && python3 manage.py migrate

CMD ["gunicorn","smitci.wsgi:application","--bind=0.0.0.0:8000"]