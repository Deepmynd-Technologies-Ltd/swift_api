#!/bin/sh

set -o errexit  # Exit immediately if a command exits with a non-zero status

python manage.py makemigrations
python manage.py showmigrations
python manage.py migrate
python manage.py collectstatic --no-input || echo "Static collection failed, continuing..."

# Corrected if statement syntax
# if [ "$CREATE_SUPERUSER" = "true" ]; then
#     echo "Creating superuser"
#     python manage.py createsuperuser --no-input
# fi
