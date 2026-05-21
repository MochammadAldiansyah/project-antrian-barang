"""
WSGI config for antrianbarang project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'antrianbarang.settings')

application = get_wsgi_application()

# Auto-migrate on Vercel serverless startup (hanya jika ada DATABASE_URL PostgreSQL)
# Ini memastikan tabel baru (seperti DummyResi) selalu ada di production
if os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL'):
    try:
        from django.core.management import call_command
        call_command('migrate', '--run-syncdb', verbosity=0)
    except Exception as e:
        import sys
        print(f"[WSGI] Auto-migrate warning: {e}", file=sys.stderr)
