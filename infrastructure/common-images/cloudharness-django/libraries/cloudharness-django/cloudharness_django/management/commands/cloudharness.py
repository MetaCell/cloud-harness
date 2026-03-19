from django.core.management.base import BaseCommand, CommandError
from cloudharness_django.services import get_user_service


class Command(BaseCommand):
    help = 'CloudHarness management commands'

    def add_arguments(self, parser):
        parser.add_argument(
            'subcommand',
            type=str,
            help='Subcommand to run (e.g., sync)',
        )

    def handle(self, *args, **options):
        subcommand = options.get('subcommand')

        if subcommand == 'sync':
            self.sync_keycloak()
        else:
            raise CommandError(f'Unknown subcommand: {subcommand}')

    def sync_keycloak(self):
        """Sync Keycloak users and groups."""
        try:
            get_user_service().sync_kc_users_groups()
            self.stdout.write(self.style.SUCCESS('Keycloak users & groups synced successfully.'))
        except Exception as e:
            raise CommandError(f'Failed to sync Keycloak users & groups: {str(e)}')
