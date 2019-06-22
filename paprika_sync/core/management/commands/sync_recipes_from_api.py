import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from paprika_sync.core.models import PaprikaAccount


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "For all PaprikaAccounts in successful sync/import state that haven't been updated in 24 hours, sync all recipes, adding/updating/expiring as needed. Intended to run on cron regularly (e.g. hourly)."

    def handle(self, *args, **options):
        days_ago = 1
        accounts_to_sync = PaprikaAccount.objects.filter(
            import_sync_status=PaprikaAccount.SYNC_SUCCESS,
            sync_failure_count__lt=5,
            last_synced__lte=timezone.now() - timezone.timedelta(days=days_ago),
        )

        for pa in accounts_to_sync:
            self.sync_account(pa)

    def sync_account(self, paprika_account):
        logger.info('Starting regular background sync of recipes for %s', paprika_account)
        # Change status to 'in progress'
        paprika_account.start_sync_recipes()
        paprika_account.save()

        paprika_account.sync_recipes()
        paprika_account.save()
