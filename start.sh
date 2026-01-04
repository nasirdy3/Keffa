#!/bin/bash

# Start Celery Worker in the background with memory optimizations
celery -A kefa_project worker -l info --concurrency 1 --max-tasks-per-child 10 &

# Start Celery Beat in the background
celery -A kefa_project beat -l info &

# Start the Web Server (Gunicorn) with memory optimizations
# --preload saves memory by sharing code between workers
gunicorn kefa_project.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --preload
