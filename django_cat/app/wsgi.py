"""
WSGI config for app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from app.launch import main
import threading


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

def custom_wsgi_application():
    threading.Thread(target=main).start()
    return get_wsgi_application()

application = custom_wsgi_application()
