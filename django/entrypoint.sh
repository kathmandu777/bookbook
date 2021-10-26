#!/bin/bash

if [ "$DB" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# python manage.py flush --noinput
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# hot reload
uwsgi --ini /code/uwsgi.ini

exec "$@"