import logging

from django.core.management.base import BaseCommand

from paprika_sync.core.models import PaprikaAccount


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'For all PaprikaAccounts with requested or failed sync, sync all recipes, adding/updating/expiring as needed. Intended to run on cron every minute.'

    def handle(self, *args, **options):
        accounts_to_sync = PaprikaAccount.objects.filter(
            import_sync_status__in=(PaprikaAccount.SYNC_REQUESTED, PaprikaAccount.SYNC_FAILURE),
            sync_failure_count__lt=5,
        )

        for pa in accounts_to_sync:
            self.sync_account(pa)

    def sync_account(self, paprika_account):
        logger.info('Starting requested sync of recipes for %s', paprika_account)
        # Change status to 'in progress'
        paprika_account.start_sync_recipes()
        paprika_account.save()

        paprika_account.sync_recipes()
        paprika_account.save()
