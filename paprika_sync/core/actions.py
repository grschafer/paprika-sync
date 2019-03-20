import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .api import get_recipes, get_recipe
from .models import PaprikaAccount, Recipe, NewsItem
from .serializers import RecipeSerializer


logger = logging.getLogger(__name__)


# TODO: Move (most of) these to be methods on PaprikaAccount?


def import_account(user, username, password, alias):
    logger.info('start import_account for %s (%s)', username, alias)
    # in transaction:
    # Create PaprikaAccount, fetch all recipes and create Recipes in db for them
    with transaction.atomic():
        pa = PaprikaAccount.objects.create(user=user, username=username, password=password, alias=alias)
        recipes = get_recipes(pa)
        if len(recipes) > settings.RECIPE_THRESHOLD_TO_DEFER_IMPORT:
            logger.info('deferring import of %s recipes', len(recipes))
            pa.import_status = PaprikaAccount.IMPORT_DEFERRED
        else:
            logger.info('importing %s recipes', len(recipes))
            import_recipes(pa, recipes)
            pa.import_status = PaprikaAccount.IMPORT_SUCCESS
        pa.save()
    return pa


def import_recipes(paprika_account, recipes):
    starting_recipe_count = paprika_account.recipes.count()
    for recipe in recipes:
        print('.', end='')
        uid = recipe['uid']
        recipe_detail = get_recipe(uid, paprika_account)
        recipe_name = recipe_detail['name']
        if paprika_account.recipes.filter(uid=uid).exists():
            logger.info('Recipe already exists in %s: %s %s', paprika_account, recipe_name, uid)
            continue

        recipe_detail['paprika_account'] = paprika_account.id
        rs = RecipeSerializer(data=recipe_detail)
        if rs.is_valid():
            rs.save()
        else:
            logger.error('Invalid recipe %s: %s', recipe_name, rs.errors)
            # TODO: collect errors and show to user?

    ending_recipe_count = paprika_account.recipes.count()
    print('Imported', ending_recipe_count - starting_recipe_count, 'recipes')

    NewsItem.objects.create(
        paprika_account=paprika_account,
        type=NewsItem.TYPE_NEW_ACCOUNT,
        payload={'num_recipes': len(recipes)},
    )


def sync_account_recipes_from_api(paprika_account):
    # Update Recipes from api, save revisions, create new NewsItems
    logger.info('start sync_account_recipes_from_api for %s', paprika_account)
    recipes = get_recipes(paprika_account)

    # Figure out what recipes were deleted from the API, if any
    db_uids = set(paprika_account.recipes.filter(date_ended__isnull=True).values_list('uid', flat=True))
    api_uids = set(r['uid'] for r in recipes)
    deleted_recipes = db_uids - api_uids

    with transaction.atomic():
        if deleted_recipes:
            to_delete = Recipe.objects.filter(paprika_account=paprika_account, uid__in=deleted_recipes)
            for recipe in to_delete:
                NewsItem.objects.create(
                    paprika_account=paprika_account,
                    type=NewsItem.TYPE_RECIPE_DELETED,
                    payload={'recipe': recipe.id},
                )
            to_delete.update(date_ended=timezone.now())

        # Look for edited or newly-added recipes
        # TODO: Speed this up by only fetching hash from database first?
        for recipe in recipes:
            print('.', end='')
            uid = recipe['uid']
            db_recipe = Recipe.objects.filter(paprika_account=paprika_account, uid=uid, date_ended__isnull=True).first()
            if db_recipe:
                if db_recipe.hash != recipe['hash']:
                    # TODO: lots of duplication of recipe creation...
                    recipe_detail = get_recipe(uid, paprika_account)
                    recipe_name = recipe_detail['name']
                    recipe_detail['paprika_account'] = paprika_account.id
                    rs = RecipeSerializer(data=recipe_detail)
                    if rs.is_valid():
                        rs.save()
                    else:
                        logger.error('Invalid recipe %s: %s', recipe_name, rs.errors)
                        # TODO: collect errors and show to user?

                    # Expire the old recipe
                    db_recipe.date_ended = timezone.now()
                    db_recipe.save()

                    # Create a NewsItem for the diff between new and old recipes
                    fields_changed = list(db_recipe.diff(rs.instance).keys())
                    NewsItem.objects.create(
                        paprika_account=paprika_account,
                        type=NewsItem.TYPE_RECIPE_EDITED,
                        payload={'fields_changed': fields_changed, 'recipe': rs.instance.id, 'previous_recipe': db_recipe.id},
                    )
                else:
                    pass  # No change in the recipe

            else:
                # Save new recipe
                recipe_detail = get_recipe(uid, paprika_account)
                recipe_name = recipe_detail['name']
                recipe_detail['paprika_account'] = paprika_account.id
                rs = RecipeSerializer(data=recipe_detail)
                if rs.is_valid():
                    rs.save()

                    NewsItem.objects.create(
                        paprika_account=paprika_account,
                        type=NewsItem.TYPE_RECIPE_ADDED,
                        payload={'recipe': rs.instance.id},
                    )
                else:
                    logger.error('Invalid recipe %s: %s', recipe_name, rs.errors)
                    # TODO: collect errors and show to user?


def compare_accounts(my_account, your_account):
    logger.info('start compare_accounts between %s and %s', my_account, your_account)
    # Collect all recipes from both accounts, determine which are common between them
    # Return: list of (Recipe, my_account_has_recipe, your_account_has_recipe, accounts_differ)
    # accounts_differ = both accounts have the recipe, but the versions do not match exactly
    pass


def clone_recipes(recipes, from_account, to_account):
    logger.info('start clone_recipes %s from %s to %s', recipes, from_account, to_account)
    # Clone the specified recipes from one account to another
    pass


def get_news_and_actions(user):
    logger.info('start get_news_and_actions for %s', user)
    # Fetch recent NewsItems and figure out contextual actions to offer for any/all of user's PaprikaAccounts
    pass
