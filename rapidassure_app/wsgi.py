"""
WSGI config for rapidassure_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rapidassure_app.settings')

application = get_wsgi_application()

# Asegurar que las tablas de la base de datos local SQLite existan al iniciar Gunicorn
try:
    from django.core.management import call_command
    from django.db import connection
    tables = connection.introspection.table_names()
    if 'tienda_categoria' not in tables:
        print("[WSGI] Tablas no encontradas en SQLite. Migrando y poblando base de datos...")
        call_command('migrate', interactive=False)
        try:
            from scripts.seed_rapidassure import run as seed_run
            seed_run()
        except Exception as seed_err:
            print(f"[WSGI] Error al poblar base de datos: {seed_err}")
        try:
            from scripts.create_superuser import run as superuser_run
            superuser_run()
        except Exception as admin_err:
            print(f"[WSGI] Error al crear superusuario: {admin_err}")
except Exception as exc:
    print(f"[WSGI] Error en auto-migración: {exc}")

