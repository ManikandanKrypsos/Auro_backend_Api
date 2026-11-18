"""python manage.py create_platform_admin --email you@company.com --name "Deepak" [--password …]"""
import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError

from tenants.models import PlatformAdmin


class Command(BaseCommand):
    help = 'Create (or reset the password of) a platform Super Admin.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--name', default='Super Admin')
        parser.add_argument('--password', help='Omit to be prompted (recommended).')

    def handle(self, *args, **opts):
        password = opts['password'] or getpass.getpass('Password: ')
        try:
            validate_password(password)
        except Exception as e:
            raise CommandError(' '.join(getattr(e, 'messages', [str(e)])))
        admin, created = PlatformAdmin.objects.get_or_create(email=opts['email'].lower(), defaults={'name': opts['name']})
        admin.set_password(password)
        admin.is_active = True
        admin.save()
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"} Super Admin {admin.email}'))
