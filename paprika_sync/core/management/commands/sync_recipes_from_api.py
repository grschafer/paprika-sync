import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from paprika_sync.core.models import PaprikaAccount
from paprika_sync.core.utils import log_start_end


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "For all PaprikaAccounts in successful sync/import state that haven't been updated in 24 hours (or sync has been requested), sync all recipes, adding/updating/expiring as needed. Intended to run on cron regularly."

    def add_arguments(self, parser):
        parser.add_argument(
            '--requested',
            action='store_true',
            help='Sync requested accounts',
        )
        parser.add_argument(
            '--exclude-synced-within',
            metavar='DAYS_AGO',
            type=int,
            default=2,
            help="Don't sync accounts synced in last DAYS_AGO days (default=2)",
        )

    @log_start_end(logger)
    def handle(self, *args, **options):
        requested = options['requested']
        if requested:
            accounts_to_sync = PaprikaAccount.objects.filter(
                import_sync_status__in=(PaprikaAccount.SYNC_REQUESTED, PaprikaAccount.SYNC_FAILURE),
                sync_failure_count__lt=5,
            )
        else:
            days_ago = options['exclude_synced_within']
            accounts_to_sync = PaprikaAccount.objects.filter(
                import_sync_status=PaprikaAccount.SYNC_SUCCESS,
                sync_failure_count__lt=5,
                last_synced__lte=timezone.now() - timezone.timedelta(days=days_ago),
            )

        for pa in accounts_to_sync:
            try:
                self.sync_account(pa)
            except Exception as e:
                pa.sync_failure_count += 1
                pa.save()

    def sync_account(self, paprika_account):
        logger.info('Starting regular background sync of recipes for %s', paprika_account)
        # Change status to 'in progress'
        paprika_account.start_sync_recipes()
        paprika_account.save()

        paprika_account.sync_recipes()
        paprika_account.save()
