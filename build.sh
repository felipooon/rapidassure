#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
mkdir -p staticfiles
python manage.py collectstatic --noinput
python manage.py migrate --noinput
# python scripts/seed_rapidassure.py || true  # DESACTIVADO: borraba los productos reales en cada deploy
python scripts/create_superuser.py || true