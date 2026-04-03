#!/usr/bin/env bash
set -e

pip install -r requirements.txt

# We ship migration files for services (0001+0002) and accounts/webhooks (0001).
# Only run makemigrations for apps that don't have shipped migrations,
# or to pick up any future model changes.
python manage.py makemigrations accounts --check 2>/dev/null || python manage.py makemigrations accounts
python manage.py makemigrations webhooks --check 2>/dev/null || python manage.py makemigrations webhooks

# Apply all migrations (services 0001 + 0002 are already committed)
python manage.py migrate --noinput

# Create static dir to avoid warning, then collect
mkdir -p static
python manage.py collectstatic --noinput

# Seed initial service categories and demo services
python manage.py seed

# Create superuser only if env vars are set and user doesn't exist
python manage.py shell << 'PYEOF'
from apps.accounts.models import User
import os
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
if email and password and not User.objects.filter(email=email).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {email} created.")
else:
    print("Superuser already exists or env vars not set, skipping.")
PYEOF
