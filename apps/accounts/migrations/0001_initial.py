import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('username', models.CharField(
                    error_messages={'unique': 'A user with that username already exists.'},
                    max_length=150,
                    unique=True,
                    validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                    verbose_name='username',
                )),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('plan', models.CharField(
                    choices=[('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')],
                    default='free',
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[('active', 'Active'), ('inactive', 'Inactive'), ('suspended', 'Suspended')],
                    default='inactive',
                    max_length=20,
                )),
                ('gumroad_sale_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('gumroad_subscription_id', models.CharField(blank=True, max_length=255, null=True)),
                ('gumroad_product_id', models.CharField(blank=True, max_length=255, null=True)),
                ('subscription_start', models.DateTimeField(blank=True, null=True)),
                ('subscription_end', models.DateTimeField(blank=True, null=True)),
                ('subscription_renewed_at', models.DateTimeField(blank=True, null=True)),
                ('setup_token', models.UUIDField(blank=True, null=True)),
                ('setup_token_expires', models.DateTimeField(blank=True, null=True)),
                ('password_set', models.BooleanField(default=False)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('language', models.CharField(default='en', max_length=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(
                    blank=True,
                    help_text='The groups this user belongs to.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    help_text='Specific permissions for this user.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'ordering': ['-created_at'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(default='📋', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='activities',
                    to='accounts.user',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
