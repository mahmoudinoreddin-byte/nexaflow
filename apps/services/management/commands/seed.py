"""
Management command: python manage.py seed
Creates initial service categories and demo services.
"""
from django.core.management.base import BaseCommand
from apps.services.models import Service, ServiceCategory


CATEGORIES = ['AI Tools', 'Analytics', 'Communication', 'Storage']

SERVICES = [
    {'name': 'AI Translator', 'desc': 'Auto-translate content for your users', 'icon': '🌍', 'cat': 'AI Tools'},
    {'name': 'FusionCore CAD Editor', 'desc': '3D CAD editor with transform gizmo, extrude, and G-Code/STL export', 'icon': '⚙️', 'cat': 'AI Tools', 'tool_slug': 'cad-editor'},
    {'name': 'Dashboard Analytics', 'desc': 'Usage statistics and behavior tracking', 'icon': '📊', 'cat': 'Analytics'},
    {'name': 'Email Automation', 'desc': 'Automated email campaigns and triggers', 'icon': '📬', 'cat': 'Communication'},
    {'name': 'AI Content Writer', 'desc': 'Generate blog posts, copies and more', 'icon': '🤖', 'cat': 'AI Tools'},
    {'name': 'Video Localizer', 'desc': 'HeyGen-powered video translation', 'icon': '🎬', 'cat': 'AI Tools'},
    {'name': 'File Storage', 'desc': 'Secure cloud file management', 'icon': '📁', 'cat': 'Storage'},
    {'name': 'AI Voice Clone', 'desc': 'ElevenLabs voice generation', 'icon': '🔊', 'cat': 'AI Tools'},
]


class Command(BaseCommand):
    help = 'Seed database with initial categories and services'

    def handle(self, *args, **kwargs):
        # Create categories
        cats = {}
        for name in CATEGORIES:
            slug = name.lower().replace(' ', '-')
            cat, created = ServiceCategory.objects.get_or_create(slug=slug, defaults={'name': name})
            cats[name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))

        # Create services
        for i, s in enumerate(SERVICES):
            svc, created = Service.objects.get_or_create(
                name=s['name'],
                defaults={
                    'description': s['desc'],
                    'icon': s['icon'],
                    'category': cats.get(s['cat']),
                    'order': i,
                    'status': Service.STATUS_ACTIVE,
                    'tool_slug': s.get('tool_slug', ''),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created service: {s["name"]}'))

        self.stdout.write(self.style.SUCCESS('✅ Seed complete!'))
