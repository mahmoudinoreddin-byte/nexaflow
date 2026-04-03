from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='WebhookLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(default='unknown', max_length=50)),
                ('gumroad_sale_id', models.CharField(blank=True, max_length=255)),
                ('email', models.EmailField(blank=True)),
                ('payload', models.JSONField(default=dict)),
                ('status', models.CharField(default='success', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-received_at'],
            },
        ),
    ]
