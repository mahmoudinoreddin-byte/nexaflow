#!/usr/bin/env bash
set -e

pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py shell << 'EOF'
from apps.accounts.models import User
import os
email = os.environ['DJANGO_SUPERUSER_EMAIL']
username = os.environ['DJANGO_SUPERUSER_USERNAME']
password = os.environ['DJANGO_SUPERUSER_PASSWORD']
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {email} created.")
else:
    print(f"Superuser {email} already exists, skipping.")
EOF
