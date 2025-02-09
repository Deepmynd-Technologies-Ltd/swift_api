#!/bin/sh

set -o errexit
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input


if [[$CREATE_SUPERUSER == "true"]];
then
    echo "Creating superuser"
    python manage.py createsuperuser --no-input
fi
