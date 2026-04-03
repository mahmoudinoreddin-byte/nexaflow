#!/usr/bin/env bash
set -e

pip install -r requirements.txt

# Generate migration files for all custom apps
python manage.py makemigrations accounts
python manage.py makemigrations services
python manage.py makemigrations webhooks

# Apply all migrations
python manage.py migrate --noinput

# Create static dir to avoid warning, then collect
mkdir -p static
python manage.py collectstatic --noinput

# Create superuser only if not already exists
python manage.py shell << 'EOF'
from apps.accounts.models import User
import os
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
if email and not User.objects.filter(email=email).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {email} created.")
else:
    print(f"Superuser already exists or email not set, skipping.")
EOF
