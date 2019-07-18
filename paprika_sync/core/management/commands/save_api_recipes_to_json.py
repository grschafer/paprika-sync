import json
import logging

from django.core.management.base import BaseCommand

from paprika_sync.core.models import PaprikaAccount
from paprika_sync.core.utils import log_start_end


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Download recipes from Paprika API and save to json files (named <id>_recipes.json and <id>_categories.json)'

    def add_arguments(self, parser):
        parser.add_argument(
            'paprika_account_id',
            help='ID of PaprikaAccount to download recipes for',
        )

    @log_start_end(logger)
    def handle(self, *args, **options):
        pa_id = options['paprika_account_id']
        logger.info('Starting API download of recipes and categories for PaprikaAccount %s', pa_id)

        pa = PaprikaAccount.objects.get(id=pa_id)
        with open('{}_recipes.json'.format(pa_id), 'wt') as fout_recipes, open('{}_categories.json'.format(pa_id), 'wt') as fout_categories:

            recipe_list = pa.get_recipes()
            logger.info('Got list of %s recipes', len(recipe_list))
            recipes = []
            for recipe in recipe_list:
                recipes.append(pa.get_recipe(recipe['uid']))
            json.dump(recipes, fout_recipes, indent=2)
            logger.info('Wrote %s recipes to %s', len(recipes), fout_recipes.name)

            categories = pa.get_categories()
            json.dump(categories, fout_categories, indent=2)
            logger.info('Wrote %s categories to %s', len(categories), fout_categories.name)
