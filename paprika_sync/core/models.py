import logging

import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone

from django_fsm import FSMField, transition
from django_fsm_log.decorators import fsm_log_by


logger = logging.getLogger(__name__)


# Paprika API docs: https://gist.github.com/mattdsteele/7386ec363badfdeaad05a418b9a1f30a
RECIPES_URL = 'https://www.paprikaapp.com/api/v1/sync/recipes/'
RECIPE_URL = 'https://www.paprikaapp.com/api/v1/sync/recipe/{uid}/'


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PaprikaAccount(BaseModel):
    NEW_ACCOUNT, IMPORT_DEFERRED, IMPORT_INPROGRESS = 'new_account', 'import_deferred', 'import_inprogress'
    SYNC_REQUESTED, SYNC_INPROGRESS, SYNC_SUCCESS = 'sync_requested', 'sync_inprogress', 'success'
    IMPORT_FAILURE, SYNC_FAILURE = 'import_failure', 'sync_failure'
    IMPORT_SYNC_STATUS_CHOICES = (
        (NEW_ACCOUNT, NEW_ACCOUNT),
        (IMPORT_DEFERRED, IMPORT_DEFERRED),
        (IMPORT_INPROGRESS, IMPORT_INPROGRESS),
        (SYNC_REQUESTED, SYNC_REQUESTED),
        (SYNC_INPROGRESS, SYNC_INPROGRESS),
        (SYNC_SUCCESS, SYNC_SUCCESS),
        (IMPORT_FAILURE, IMPORT_FAILURE),
        (SYNC_FAILURE, SYNC_FAILURE),
    )
    IMPORT_SYNC_STATUS_CHOICES_LIST = (NEW_ACCOUNT, IMPORT_DEFERRED, IMPORT_INPROGRESS, SYNC_REQUESTED, SYNC_INPROGRESS, SYNC_SUCCESS, IMPORT_FAILURE, SYNC_FAILURE)

    user = models.ForeignKey(get_user_model(), related_name='paprika_accounts', on_delete=models.CASCADE)
    username = models.CharField(max_length=150, unique=True, help_text='Username to login to paprika')
    password = models.CharField(max_length=128, help_text='Password to login to paprika')
    alias = models.CharField(max_length=150, unique=True, help_text='Name to associate with this account in news feed items (e.g. Alice, Bob)')

    import_sync_status = FSMField(choices=IMPORT_SYNC_STATUS_CHOICES, default=NEW_ACCOUNT, protected=True, help_text='Status of importing/syncing recipes')
    last_synced = models.DateTimeField(null=True, help_text='When this account was last synced with the API')
    sync_failure_count = models.PositiveSmallIntegerField(default=0, help_text='Incremented for failures, to stop retrying if we are failing repeatedly')

    ##########################################################################
    # Transitions
    ##########################################################################

    @fsm_log_by
    @transition(field=import_sync_status, source=[NEW_ACCOUNT], target=IMPORT_DEFERRED)
    def defer_import_recipes(self, by=None):
        pass

    @fsm_log_by
    @transition(field=import_sync_status, source=[NEW_ACCOUNT, IMPORT_DEFERRED], target=IMPORT_INPROGRESS)
    def start_import_recipes(self, by=None):
        pass

    @fsm_log_by
    @transition(field=import_sync_status, source=[IMPORT_INPROGRESS], target=SYNC_SUCCESS, on_error=IMPORT_FAILURE)
    def import_recipes(self, recipes, by=None):
        from .serializers import RecipeSerializer
        try:
            starting_recipe_count = self.recipes.count()

            for recipe in recipes:
                print('.', end='')
                uid = recipe['uid']
                recipe_detail = self.get_recipe(uid)
                recipe_name = recipe_detail['name']
                if self.recipes.filter(uid=uid).exists():
                    logger.info('Recipe already exists in %s: %s %s', self, recipe_name, uid)
                    continue

                recipe_detail['paprika_account'] = self.id
                rs = RecipeSerializer(data=recipe_detail)
                if rs.is_valid():
                    rs.save()
                else:
                    logger.error('Invalid recipe %s: %s', recipe_name, rs.errors)
                    # TODO: collect errors and show to user?

            ending_recipe_count = self.recipes.count()
            logger.info('Imported %s recipes', ending_recipe_count - starting_recipe_count)

            NewsItem.objects.create(
                paprika_account=self,
                type=NewsItem.TYPE_NEW_ACCOUNT,
                payload={'num_recipes': len(recipes)},
            )
        except Exception as e:
            logger.exception('Import recipes for PaprikaAccount %s failed: %s', self, e)
            raise  # go to IMPORT_FAILURE state
        else:
            # Import succeeded, reset failure count
            self.last_synced = timezone.now()
            self.sync_failure_count = 0
            self.save()

    @fsm_log_by
    @transition(field=import_sync_status, source=[SYNC_SUCCESS], target=SYNC_REQUESTED)
    def request_sync_recipes(self, by=None):
        pass

    @fsm_log_by
    @transition(field=import_sync_status, source=[SYNC_SUCCESS, SYNC_REQUESTED], target=SYNC_INPROGRESS)
    def start_sync_recipes(self, by=None):
        pass

    @fsm_log_by
    @transition(field=import_sync_status, source=[SYNC_INPROGRESS], target=SYNC_SUCCESS, on_error=SYNC_FAILURE)
    def sync_recipes(self, by=None):
        from .serializers import RecipeSerializer
        # Update Recipes from api, save revisions, create new NewsItems
        logger.info('start sync_account_recipes_from_api for %s', self)
        recipes = self.get_recipes()

        # Figure out what recipes were deleted from the API, if any
        db_uids = set(self.recipes.filter(date_ended__isnull=True).values_list('uid', flat=True))
        api_uids = set(r['uid'] for r in recipes)
        deleted_recipes = db_uids - api_uids

        try:
            if deleted_recipes:
                to_delete = Recipe.objects.filter(paprika_account=self, uid__in=deleted_recipes)
                for recipe in to_delete:
                    NewsItem.objects.create(
                        paprika_account=self,
                        type=NewsItem.TYPE_RECIPE_DELETED,
                        payload={'recipe': recipe.id},
                    )
                to_delete.update(date_ended=timezone.now())

            # Look for edited or newly-added recipes
            # TODO: Speed this up by only fetching hash from database first?
            for recipe in recipes:
                print('.', end='')
                uid = recipe['uid']
                db_recipe = Recipe.objects.filter(paprika_account=self, uid=uid, date_ended__isnull=True).first()
                if db_recipe:
                    if db_recipe.hash != recipe['hash']:
                        # TODO: lots of duplication of recipe creation...
                        recipe_detail = self.get_recipe(uid)
                        recipe_name = recipe_detail['name']
                        recipe_detail['paprika_account'] = self.id
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
                            paprika_account=self,
                            type=NewsItem.TYPE_RECIPE_EDITED,
                            payload={'fields_changed': fields_changed, 'recipe': rs.instance.id, 'previous_recipe': db_recipe.id},
                        )
                    else:
                        pass  # No change in the recipe

                else:
                    # Save new recipe
                    recipe_detail = self.get_recipe(uid)
                    recipe_name = recipe_detail['name']
                    recipe_detail['paprika_account'] = self.id
                    rs = RecipeSerializer(data=recipe_detail)
                    if rs.is_valid():
                        rs.save()

                        NewsItem.objects.create(
                            paprika_account=self,
                            type=NewsItem.TYPE_RECIPE_ADDED,
                            payload={'recipe': rs.instance.id},
                        )
                    else:
                        logger.error('Invalid recipe %s: %s', recipe_name, rs.errors)
                        # TODO: collect errors and show to user?

        except Exception as e:
            logger.exception('Sync recipes for PaprikaAccount %s failed: %s', self, e)
            raise  # go to SYNC_FAILURE state
        else:
            # Sync succeeded, reset failure count
            self.last_synced = timezone.now()
            self.sync_failure_count = 0
            self.save()

    ##########################################################################
    # End Transitions
    ##########################################################################

    ##########################################################################
    # Account actions
    ##########################################################################
    @classmethod
    def import_account(cls, user, username, password, alias):
        logger.info('start import_account for %s (%s)', username, alias)
        # in transaction:
        # Create PaprikaAccount, fetch all recipes and create Recipes in db for them
        pa = PaprikaAccount.objects.create(user=user, username=username, password=password, alias=alias)
        recipes = pa.get_recipes()

        if len(recipes) > settings.RECIPE_THRESHOLD_TO_DEFER_IMPORT:
            logger.info('Deferring import of %s recipes', len(recipes))
            pa.defer_import(by=user)
            pa.save()
        else:
            logger.info('Importing %s recipes', len(recipes))
            pa.start_import_recipes(by=user)
            pa.save()  # Mark account as importing
            pa.import_recipes(recipes, by=user)
            pa.save()
        return pa

    def compare_accounts(self, other_account):
        logger.info('start compare_accounts between %s and %s', self, other_account)
        # Collect all recipes from both accounts, determine which are common between them
        # Return: list of (Recipe, my_account_has_recipe, your_account_has_recipe, accounts_differ)
        # accounts_differ = both accounts have the recipe, but the versions do not match exactly
        pass

    def clone_recipes(self, recipes, from_account):
        logger.info('start clone_recipes %s from %s to %s', recipes, from_account, self)
        # Clone the specified recipes from one account to another
        pass

    def get_news_and_actions(self):
        logger.info('start get_news_and_actions for paprika account %s', self)
        # TODO: should this method be at the user-level? most likely, users will only have 1 PaprikaAccount
        # Fetch recent NewsItems and figure out contextual actions to offer for any/all of user's PaprikaAccounts
        pass
    ##########################################################################
    # End Account actions
    ##########################################################################

    ##########################################################################
    # Paprika API helpers
    ##########################################################################

    def get_recipes(self):
        resp = requests.get(RECIPES_URL, auth=(self.username, self.password))
        resp.raise_for_status()
        return resp.json()['result']

    def get_recipe(self, uid):
        url = RECIPE_URL.format(uid=uid)
        resp = requests.get(url, auth=(self.username, self.password))
        resp.raise_for_status()
        return resp.json()['result']
    ##########################################################################
    # End Paprika API helpers
    ##########################################################################

    def __str__(self):
        return '{} ({})'.format(self.alias, self.username)


class Recipe(BaseModel):
    paprika_account = models.ForeignKey('core.PaprikaAccount', related_name='recipes', on_delete=models.CASCADE)
    uid = models.CharField(max_length=200, db_index=True)
    date_ended = models.DateTimeField(null=True, db_index=True, help_text='Date when this version of the Recipe was superseded (unset if this is the active Recipe for this uid)')
    hash = models.CharField(max_length=200)
    photo_hash = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    # TODO: do these need to be nullable?
    image_url = models.URLField(max_length=200)
    # TODO: add other fields (ingreds, directions, rating, source, categories, etc... anything that can change and should be flagged in a NewsItem)
    # TODO: add a 'deleted' flag?
    IGNORE_FIELDS_IN_DIFF = {'id', 'created_date', 'modified_date', 'paprika_account', 'date_ended'}

    def diff(self, other):
        'Diffs 2 Recipes, returning {field_name: True, ...} containing all fields changed'
        fields_changed = {}
        for field in Recipe._meta.get_fields():
            if field.name not in Recipe.IGNORE_FIELDS_IN_DIFF:
                if getattr(self, field.name) != getattr(other, field.name):
                    fields_changed[field.name] = True

        return fields_changed

    def __str__(self):
        return self.name


class NewsItem(BaseModel):
    TYPE_NEW_ACCOUNT, TYPE_RECIPE_ADDED, TYPE_RECIPE_EDITED, TYPE_RECIPE_DELETED = 'new_account', 'recipe_added', 'recipe_edited', 'recipe_deleted'
    TYPE_CHOICES = (
        (TYPE_NEW_ACCOUNT, TYPE_NEW_ACCOUNT),
        (TYPE_RECIPE_ADDED, TYPE_RECIPE_ADDED),
        (TYPE_RECIPE_EDITED, TYPE_RECIPE_EDITED),
        (TYPE_RECIPE_DELETED, TYPE_RECIPE_DELETED),
    )
    TYPE_CHOICES_LIST = (TYPE_NEW_ACCOUNT, TYPE_RECIPE_ADDED, TYPE_RECIPE_EDITED, TYPE_RECIPE_DELETED)
    paprika_account = models.ForeignKey('core.PaprikaAccount', related_name='+', on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    payload = JSONField(default=dict, help_text='Specifies details (e.g. what fields of a recipe were updated)')

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return '{} by {}'.format(self.type, self.paprika_account)
