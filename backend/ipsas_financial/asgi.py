"""
ASGI config for IPSAS Financial Software project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ipsas_financial.settings')

application = get_asgi_application()
