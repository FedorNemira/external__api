import os
import sys

from django.core.wsgi import get_wsgi_application

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_PATH))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_wsgi_application()
