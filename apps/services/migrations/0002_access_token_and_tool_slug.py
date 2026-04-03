"""
Migration 0002: adds access_token to UserService + tool_slug to Service.

YOUR CASE (existing deployment, already ran old 0001):
  Run:  python manage.py migrate
  This will ALTER the two tables and backfill access tokens for existing rows.

Fresh install:
  0001_initial already includes these columns. Django will mark this migration
  as applied without touching the DB (the columns already exist).
"""
import uuid
from django.db import migrations, models


def backfill_access_tokens(apps, schema_editor):
    """Assign a unique UUID to every existing UserService that lacks one."""
    UserService = apps.get_model('services', 'UserService')
    rows = UserService.objects.all()
    for us in rows:
        if not us.access_token:
            us.access_token = uuid.uuid4()
            us.save(update_fields=['access_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        # Add tool_slug to Service
        migrations.AddField(
            model_name='service',
            name='tool_slug',
            field=models.SlugField(
                blank=True,
                default='',
                help_text='If set, opens a built-in tool page (e.g. cad-editor). Overrides url.',
            ),
            preserve_default=False,
        ),
        # Add access_token to UserService (nullable first so existing rows are ok)
        migrations.AddField(
            model_name='userservice',
            name='access_token',
            field=models.UUIDField(null=True, blank=True, editable=False),
        ),
        # Backfill all existing rows with a UUID
        migrations.RunPython(backfill_access_tokens, migrations.RunPython.noop),
        # Now make it non-nullable and unique
        migrations.AlterField(
            model_name='userservice',
            name='access_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
