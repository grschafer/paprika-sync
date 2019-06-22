import logging

from django.core.management.base import BaseCommand

from paprika_sync.core.models import PaprikaAccount


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'For any PaprikaAccounts deferred or failed account imports, import all their recipes. Intended to run on cron every minute.'

    def handle(self, *args, **options):
        accounts_to_import = PaprikaAccount.objects.filter(
            import_sync_status__in=(PaprikaAccount.IMPORT_DEFERRED, PaprikaAccount.IMPORT_FAILURE),
            sync_failure_count__lt=5,
        )
        for pa in accounts_to_import:
            try:
                self.import_account(pa)
            except Exception as e:
                pa.sync_failure_count += 1
                pa.save()

    def import_account(self, paprika_account):
        logger.info('Starting background import of recipes for %s', paprika_account)
        paprika_account.start_import_recipes()
        paprika_account.save()

        recipes = paprika_account.get_recipes()
        paprika_account.import_recipes(recipes)
        paprika_account.save()
