#!/bin/bash

# Start Celery Worker in the background
celery -A kefa_project worker -l info &

# Start Celery Beat in the background
celery -A kefa_project beat -l info &

# Start the Web Server (Gunicorn)
# This is the main process that keeps the container alive
gunicorn kefa_project.wsgi:application --bind 0.0.0.0:$PORT
