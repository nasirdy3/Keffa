#!/bin/bash

# 1. Start Celery Worker (Background)
# --concurrency 1 is vital for the 512MB RAM limit
celery -A kefa_project worker -l info --concurrency 1 --max-tasks-per-child 10 &

# 2. Start Celery Beat (Background)
celery -A kefa_project beat -l info &

# 3. Start the Web Server using Daphne (Supports Channels + Web)
daphne -b 0.0.0.0 -p $PORT kefa_project.asgi:application

