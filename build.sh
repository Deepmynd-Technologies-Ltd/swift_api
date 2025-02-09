#!/bin/sh

python manage.py migrate --no-input
python manage.py collectstatic --no-input
gunicorn core.wsgi --bind 0.0.0.0:8000

if [[$CREATE_SUPERUSER == "true"]];
then
    echo "Creating superuser"
    python manage.py createsuperuser --no-input
fi
