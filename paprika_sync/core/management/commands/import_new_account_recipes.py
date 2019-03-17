import logging

from django.core.management.base import BaseCommand

from paprika_sync.core.actions import import_recipes
from paprika_sync.core.api import get_recipes
from paprika_sync.core.models import PaprikaAccount


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'For any PaprikaAccounts with import_status=deferred, import all their recipes. Intended to run on cron every minute.'

    def handle(self, *args, **options):
        for pa in PaprikaAccount.objects.filter(import_status=PaprikaAccount.IMPORT_DEFERRED):
            logger.info('Starting background import of recipes for %s', pa)
            pa.import_status = PaprikaAccount.IMPORT_INPROGRESS
            pa.save()

            recipes = get_recipes(pa)
            import_recipes(pa, recipes)
            pa.import_status = PaprikaAccount.IMPORT_SUCCESS
            pa.save()
