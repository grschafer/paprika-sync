import logging

from django.core.management.base import BaseCommand

from paprika_sync.core.actions import sync_account_recipes_from_api
from paprika_sync.core.models import PaprikaAccount


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'For all PaprikaAccounts with import_status=success, sync all recipes, adding/updating/expiring as needed. Intended to run on cron regularly.'

    def handle(self, *args, **options):
        for pa in PaprikaAccount.objects.filter(import_status=PaprikaAccount.IMPORT_SUCCESS):
            logger.info('Starting background sync of recipes for %s', pa)
            sync_account_recipes_from_api(pa)
