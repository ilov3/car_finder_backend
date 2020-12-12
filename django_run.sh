#!/bin/bash
set -x

python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
#gunicorn -b 0.0.0.0:8000 car_finder_backend.wsgi