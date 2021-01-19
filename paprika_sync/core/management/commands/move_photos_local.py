import logging
import os.path
import time

from django.core.management.base import BaseCommand

from paprika_sync.core.models import Recipe
from paprika_sync.core.utils import log_start_end


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ensure all recipes have a local copy of the recipe photo"

    @log_start_end(logger)
    def handle(self, *args, **options):
        recipes = Recipe.objects.exclude(photo_url='')

        # TODO: hardcoded
        recipes = recipes.filter(paprika_account_id=1)
        i = 0

        logger.info("Ensuring photos available locally for %s recipes", recipes.count())
        for recipe in recipes:
            path = recipe.get_photo_filepath()
            if not os.path.exists(path):
                logger.info("Downloading photo for Recipe %s to %s", recipe, path)
                recipe.download_photo()
            time.sleep(0.1)

            # TODO: remove
            i += 1
            if i > 5:
                break
