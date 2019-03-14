import logging

from django.db import transaction

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
        for recipe in recipes:
            recipe_detail = get_recipe(recipe['uid'], pa)
            recipe_detail['paprika_account'] = pa.id
            rs = RecipeSerializer(data=recipe_detail)
            if rs.is_valid():
                rs.save()
            else:
                # TODO: log and collect errors
                pass
    return pa
    # TODO: create NewsItem for new account sync-ing


def sync_account_recipes_from_api(paprika_account):
    logger.info('start sync_account_recipes_from_api for %s', paprika_account)
    # Update Recipes from api, save revisions, create new NewsItems
    pass


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
