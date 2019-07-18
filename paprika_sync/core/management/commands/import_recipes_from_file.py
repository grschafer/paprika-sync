import json
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from paprika_sync.core.models import PaprikaAccount
from paprika_sync.core.serializers import RecipeSerializer, CategorySerializer
from paprika_sync.core.utils import log_start_end


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import all recipes from file to specified PaprikaAccount'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            help='Path to json file containing list of all recipes',
        )
        parser.add_argument(
            '--categories-file',
            help='Path to json file containing list of all categories',
        )
        parser.add_argument(
            'paprika_account_id',
            type=int,
            help='ID of PaprikaAccount to import recipes to',
        )
        parser.add_argument(
            '-r', '--remove',
            action='store_true',
            help="Removes all of account's existing recipes before importing",
        )

    @log_start_end(logger)
    def handle(self, *args, **options):
        recipes_file = options['file']
        categories_file = options['categories_file']
        pa_id = options['paprika_account_id']
        wipe_account = options['remove']

        logger.info('Starting import for PaprikaAccount id %s from %s, wipe_account=%s', pa_id, recipes_file, wipe_account)

        pa = PaprikaAccount.objects.get(id=pa_id)
        with open(recipes_file, 'rt') as fin:
            recipes = json.load(fin)

        logger.info('Found %s recipes to import to %s', len(recipes), pa)

        categories = []
        if categories_file:
            with open(categories_file, 'rt') as fin:
                categories = json.load(fin)
            logger.info('Found %s categories to import to %s', len(categories), pa)

        with transaction.atomic():
            if wipe_account:
                pa.recipes.all().delete()
                pa.categories.all().delete()

            for category in categories:
                category['paprika_account'] = pa.id
                cs = CategorySerializer(data=category)
                if cs.is_valid():
                    cs.save()
                else:
                    logger.warning('Failed to import category %s (%s) due to errors: %s', category['uid'], category['name'], cs.errors)

            for recipe in recipes:
                # Remove categories if we're not bothering to import them
                if not categories:
                    recipe['categories'] = []

                recipe['paprika_account'] = pa.id
                rs = RecipeSerializer(data=recipe)
                if rs.is_valid():
                    rs.save()
                else:
                    logger.warning('Failed to import recipe %s (%s) due to errors: %s', recipe['uid'], recipe['name'], rs.errors)

                # recipe_field_names = set([f.name for f in Recipe._meta.fields])
                # Recipe.objects.create(
                #     paprika_account=pa,
                #     **{k: v for k, v in recipe.items() if k in recipe_field_names},
                # )

            logger.info('Finished recipe import successfully')
            # transaction.set_rollback(True)
