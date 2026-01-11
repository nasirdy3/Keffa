"""
WSGI config for kefa_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kefa_project.settings')

# PRODUCTION FIX: Ensure settings are loaded before application starts
from django.conf import settings
settings.DEBUG  # Force settings load

application = get_wsgi_application()

