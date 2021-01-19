import gzip
import hashlib
import json
import logging
import os.path
import shutil
from urllib.parse import urlparse

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
CATEGORIES_URL = 'https://www.paprikaapp.com/api/v1/sync/categories/'


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
    username = models.CharField(max_length=150, unique=True, verbose_name='Paprika Cloud Sync Email', help_text='Email to login to Paprika Cloud Sync')
    password = models.CharField(max_length=128, verbose_name='Paprika Cloud Sync Password', help_text='Password to login to Paprika Cloud Sync')
    alias = models.CharField(max_length=150, unique=True, verbose_name="Name", help_text='Your name, for displaying in news feed items (e.g. "Alice added recipe XYZ", "Bob rated recipe Y 5 stars")')

    import_sync_status = FSMField(choices=IMPORT_SYNC_STATUS_CHOICES, default=NEW_ACCOUNT, protected=True, help_text='Status of importing/syncing recipes')
    last_synced = models.DateTimeField(null=True, help_text='When this account was last synced with the API')
    sync_failure_count = models.PositiveSmallIntegerField(default=0, help_text='Incremented for failures, to stop retrying if we are failing repeatedly')

    ##########################################################################
    # Transitions
    ##########################################################################

    @fsm_log_by
    @transition(field=import_sync_status, source=[NEW_ACCOUNT], target=IMPORT_DEFERRED)
    def defer_import_recipes(self, by=None, **kwargs):
        pass

    @fsm_log_by
    @transition(field=import_sync_status, source=[NEW_ACCOUNT, IMPORT_DEFERRED], target=IMPORT_INPROGRESS)
    def start_import_recipes(self, by=None, **kwargs):
        pass

    @fsm_log_by
    @transition(field=import_sync_status, source=[IMPORT_INPROGRESS], target=SYNC_SUCCESS, on_error=IMPORT_FAILURE)
    def import_recipes(self, recipes, by=None, **kwargs):
        logger.info('start import_recipes for %s', self)
        starting_recipe_count = self.recipes.count()
        self._sync_recipes(recipes, make_news_items=False)
        ending_recipe_count = self.recipes.count()
        logger.info('Imported %s recipes', ending_recipe_count - starting_recipe_count)

        NewsItem.objects.create(
            paprika_account=self,
            type=NewsItem.TYPE_NEW_ACCOUNT,
            payload={'num_recipes': len(recipes)},
        )

    @fsm_log_by
    @transition(field=import_sync_status, source=[SYNC_SUCCESS], target=SYNC_REQUESTED)
    def request_sync_recipes(self, by=None, **kwargs):
        pass

    @fsm_log_by
    @transition(field=import_sync_status, source=[SYNC_SUCCESS, SYNC_REQUESTED, SYNC_FAILURE], target=SYNC_INPROGRESS)
    def start_sync_recipes(self, by=None, **kwargs):
        pass

    @fsm_log_by
    @transition(field=import_sync_status, source=[SYNC_INPROGRESS], target=SYNC_SUCCESS, on_error=SYNC_FAILURE)
    def sync_recipes(self, by=None, **kwargs):
        logger.info('start sync_recipes for %s', self)
        recipes = self.get_recipes()
        self._sync_recipes(recipes)

    def _sync_recipes(self, recipes, make_news_items=True):
        # Sync categories, so we can import recipes that reference them
        try:
            self.sync_categories()
        except Exception as e:
            logger.exception('Sync categories for PaprikaAccount %s failed: %s', self, e)
            raise  # go to SYNC_FAILURE or IMPORT_FAILURE state

        from .serializers import RecipeSerializer
        # Update Recipes from api, save revisions, create new NewsItems

        # Figure out what recipes were deleted from the API, if any
        db_uids = set(self.recipes.values_list('uid', flat=True))
        api_uids = set(r['uid'] for r in recipes)
        deleted_recipes = db_uids - api_uids

        try:
            if deleted_recipes:
                to_delete = Recipe.objects.filter(paprika_account=self, uid__in=deleted_recipes)
                if make_news_items:
                    for recipe in to_delete:
                        NewsItem.objects.create(
                            recipe=recipe,
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
                db_recipe = self.all_recipes.filter(date_ended__isnull=True, uid=uid).last()
                if db_recipe:
                    if db_recipe.hash != recipe['hash']:
                        # TODO: lots of duplication of recipe creation...
                        recipe_detail = self.get_recipe(uid)
                        recipe_name = recipe_detail['name']
                        recipe_detail['paprika_account'] = self.id
                        rs = RecipeSerializer(data=recipe_detail)
                        if rs.is_valid():
                            rs.save()  # Also downloads recipe photo

                            # Expire the old recipe
                            db_recipe.date_ended = timezone.now()
                            db_recipe.save()

                            if make_news_items:
                                if rs.instance.in_trash and not db_recipe.in_trash:
                                    NewsItem.objects.create(
                                        recipe=rs.instance,
                                        previous_recipe=db_recipe,
                                        paprika_account=self,
                                        type=NewsItem.TYPE_RECIPE_DELETED,
                                        payload={'recipe': rs.instance.id, 'previous_recipe': db_recipe.id},
                                    )
                                else:
                                    # Create a NewsItem for the diff between new and old recipes
                                    fields_changed = list(db_recipe.diff(rs.instance).keys())
                                    if fields_changed:
                                        if 'rating' in fields_changed:
                                            NewsItem.objects.create(
                                                recipe=rs.instance,
                                                previous_recipe=db_recipe,
                                                paprika_account=self,
                                                type=NewsItem.TYPE_RECIPE_RATED,
                                                payload={'recipe': rs.instance.id, 'previous_recipe': db_recipe.id},
                                            )
                                            fields_changed.remove('rating')
                                        if fields_changed:
                                            NewsItem.objects.create(
                                                recipe=rs.instance,
                                                previous_recipe=db_recipe,
                                                paprika_account=self,
                                                type=NewsItem.TYPE_RECIPE_EDITED,
                                                payload={'fields_changed': fields_changed, 'recipe': rs.instance.id, 'previous_recipe': db_recipe.id},
                                            )
                        else:
                            logger.error('Invalid recipe %s: %s', recipe_name, rs.errors)
                            # TODO: collect errors and show to user?
                    else:
                        pass  # No change in the recipe

                else:
                    # Save new recipe
                    recipe_detail = self.get_recipe(uid)
                    recipe_name = recipe_detail['name']
                    recipe_detail['paprika_account'] = self.id
                    rs = RecipeSerializer(data=recipe_detail)
                    if rs.is_valid():
                        rs.save()  # Also downloads recipe photo

                        if make_news_items and not rs.instance.in_trash:
                            NewsItem.objects.create(
                                recipe=rs.instance,
                                paprika_account=self,
                                type=NewsItem.TYPE_RECIPE_ADDED,
                                payload={'recipe': rs.instance.id},
                            )
                    else:
                        logger.error('Invalid recipe %s: %s', recipe_name, rs.errors)
                        # TODO: collect errors and show to user?

        except Exception as e:
            logger.exception('Sync recipes for PaprikaAccount %s failed: %s', self, e)
            raise  # go to SYNC_FAILURE or IMPORT_FAILURE state
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
            pa.defer_import_recipes(by=user)
            pa.save()
        else:
            logger.info('Importing %s recipes', len(recipes))
            pa.start_import_recipes(by=user)
            pa.save()  # Mark account as importing
            pa.import_recipes(recipes, by=user)
            pa.save()
        return pa

    def sync_categories(self):
        from .serializers import CategorySerializer
        logger.info('start sync_categories for %s', self)
        categories = self.get_categories()

        for category in categories:
            category['paprika_account'] = self.id

            db_category = Category.objects.filter(paprika_account=self, uid=category['uid']).first()
            if db_category:
                # Update the instance in case it's been edited
                cs = CategorySerializer(instance=db_category, data=category)
            else:
                cs = CategorySerializer(data=category)

            if cs.is_valid():
                cs.save()
            else:
                logger.error('Invalid category %s: %s', category, cs.errors)
                # TODO: collect errors and show to user?

    def compare_accounts(self, your_account):
        logger.info('start compare_accounts between %s and %s', self, your_account)
        # Collect all recipes from both accounts, determine which are common between them
        # Return: list of (Recipe, my_account_has_recipe, your_account_has_recipe, accounts_differ)
        # accounts_differ = both accounts have the recipe, but the versions do not match exactly
        mine = {r.name: r for r in self.recipes.all()}
        yours = {r.name: r for r in your_account.recipes.all()}
        all_recipes = self.recipes.values_list('name', flat=True).union(your_account.recipes.values_list('name', flat=True)).order_by('name')
        diff_list = []
        for name in all_recipes:
            my_recipe = mine.get(name)
            your_recipe = yours.get(name)
            diff_list.append(
                (
                    name,
                    my_recipe.id if my_recipe else None,
                    your_recipe.id if your_recipe else None,
                    my_recipe.import_stable_hash != your_recipe.import_stable_hash if my_recipe and your_recipe else None,
                )
            )

        return diff_list

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

    def get_categories(self):
        resp = requests.get(CATEGORIES_URL, auth=(self.username, self.password))
        resp.raise_for_status()
        return resp.json()['result']

    def clone_recipe(self, recipe):
        '''
        Locally-captured upload (with locally-taken photo) looks like:
        {
            "uid": "CF320C3E-CEDA-489B-84DE-9B656F6BF9B3-637-00000176E20B1F11",
            "name": "Test photo upload",
            "directions": null,
            "servings": null,
            "rating": 0,
            "difficulty": null,
            "ingredients": null,
            "notes": null,
            "created": "2020-09-07 14:27:38",
            "image_url": "assets-library://asset/asset.JPG?id=5248AA42-600B-45E1-BD1D-5659976F5271&ext=JPG",
            "on_favorites": 0,
            "cook_time": null,
            "prep_time": null,
            "source": null,
            "source_url": null,
            "photo_hash": "60226292d390f4cb0846124ebf8226e2e169581dd03884b4de9606fe56cb03c3",
            "photo": "B4F1AE83-7653-40A0-A0D3-FBED43E40D9F-637-00000176E20D2E6C.jpg",
            "nutritional_info": null,
            "deleted": false,
            "scale": null,
            "categories": [],
            "hash": "f3536f18ff922635fac8fa6b682a81be8317117e0775ad909f34ae06300f5574"
        }

        From recipe scraped from site (still contains 'photo_upload' key):
        {
            "uid": "B51E04E3-A839-4EC4-A70D-32FE3AD2A0A3-673-0000017B2876D3BE",
            "name": "Sichuan Chile Oil",
            "directions": "Using a pair of kitchen shears, cut all of the chiles into 1/2-inch pieces. Toast chiles in a dry wok or saucepan over medium heat, stirring and shaking constantly, until fragrant and lightly darkened in color, about 2 minutes.\n\nTransfer toasted chiles to the bowl of a food processor or mortar and pestle, and pulse or pound until the chiles break into 1/8- to 1/4-inch pieces that resemble store-bought red-pepper flakes or flaky sea salt. (Be careful not to overprocess.) Transfer the chile flakes to a heat-proof mixing bowl.\n\nCombine oil, garlic, ginger, Sichuan peppercorns, star anise, cumin and fennel seeds in a small saucepan. Heat over low heat until gently bubbling, then cook for 10 minutes, adjusting heat to maintain the barest of bubbling.\n\nSet a fine-mesh strainer over the bowl with the chiles. Pour the hot oil through strainer over the chiles. Discard solids. Stir sugar, sesame seeds, salt and MSG, if using, into oil mixture until combined. Allow to cool, transfer to a sealed container, and let rest at room temperature overnight before using. You can store chile oil in a cool, dark pantry for a few weeks, or indefinitely in the refrigerator.",
            "servings": "Yield about 1 1/4 cups chile oil",
            "rating": 0,
            "difficulty": "",
            "ingredients": "4 dried chiles de \u00e1rbol, stems and seeds removed (see Note)\n2 dried ancho chiles, stems and seeds removed (see Note)\n1 cup neutral oil, such as canola, rice bran or soybean oil\n4 garlic cloves, smashed with the side of a knife, skins discarded\n1 (1-inch) unpeeled knob fresh ginger, smashed with the side of a knife\n1 tablespoon Sichuan peppercorns\n1 whole star anise pod\n1 teaspoon whole cumin seeds\n1 teaspoon whole fennel seeds\n1 tablespoon granulated sugar\n1 tablespoon sesame seeds (black, white or a mix)\n\u00bd teaspoon kosher salt\n\u00bc teaspoon MSG powder, such as Aji-no-moto or Ac\u2019cent (optional)",
            "notes": "",
            "created": "2020-09-07 15:08:20",
            "image_url": "https://static01.nyt.com/images/2020/07/01/dining/29Kenjirex2/29Kenjirex2-articleLarge.jpg",
            "on_favorites": 0,
            "cook_time": "15 minutes",
            "prep_time": "",
            "source": "Cooking.nytimes.com",
            "source_url": "https://cooking.nytimes.com/recipes/1021202-sichuan-chile-oil",
            "photo_hash": "89419e4f5e5b6dfb713b3417f88d8b31e2a82eb4708362d3a8687f9cce64300a",
            "photo": "951DD75F-9921-4037-AD62-92B8E59BA658-673-0000017B287DC530.jpg",
            "nutritional_info": "",
            "deleted": false,
            "scale": null,
            "categories": [],
            "hash": "de340aeed079bcd2f219ff2b8bc5cde734486765d55dec66936229ed18d1addf"
        }
        '''
        from .serializers import RecipeSerializer
        url = RECIPE_URL.format(uid=recipe.uid)

        recipe_data = RecipeSerializer(instance=recipe).data
        # TODO: hacky data fixes so the request will succeed
        recipe_data['image_url'] = None
        recipe_data['photo'] = recipe_data['photo_url'].split('/')[-1]
        recipe_data['created'] = recipe_data['created'].replace('T', ' ').replace('Z', ' ')
        del recipe_data['photo_url']
        # Clear categories because they won't match across accounts anyway
        # TODO: Look for same/similarly-named categories in the destination account?
        recipe_data['categories'] = []

        files = {'data': gzip.compress(json.dumps(recipe_data).encode())}
        if recipe.photo_url:
            photo_content = recipe.get_photo_content()
            files['photo_upload'] = (recipe_data['photo'], photo_content)

        resp = requests.post(url, auth=(self.username, self.password), files=files)
        resp.raise_for_status()
        if not resp.json().get('result', False):
            raise Exception('Cloning recipe failed! Error: '.format(resp.json().get('error', {}).get('message')))
    ##########################################################################
    # End Paprika API helpers
    ##########################################################################

    @property
    def recipes(self):
        return self.all_recipes.filter(date_ended__isnull=True).exclude(in_trash=True)

    def __str__(self):
        return '{} ({})'.format(self.alias, self.username)


class Recipe(BaseModel):
    paprika_account = models.ForeignKey('core.PaprikaAccount', related_name='all_recipes', on_delete=models.CASCADE)
    uid = models.CharField(max_length=200, db_index=True)
    date_ended = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Date when this version of the Recipe was superseded (unset if this is the active Recipe for this uid)')
    hash = models.CharField(max_length=200)
    import_stable_hash = models.CharField(max_length=200, blank=True, help_text='Hash of recipe data that is stable, even if a recipe is imported from another account')
    photo_hash = models.CharField(max_length=200, blank=True)  # Can be null if no image set
    name = models.CharField(max_length=1000, blank=True)
    photo_url = models.URLField(max_length=1000, blank=True, help_text="Thumbnail for recipe")
    ingredients = models.TextField(blank=True)
    source = models.CharField(max_length=1000, blank=True)
    total_time = models.CharField(max_length=200, blank=True)
    cook_time = models.CharField(max_length=200, blank=True)
    prep_time = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField()
    description = models.TextField(blank=True)
    source_url = models.CharField(max_length=1000, blank=True)  # Some urls are ill-formatted, so not using URLField
    difficulty = models.CharField(max_length=200, blank=True)
    directions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    nutritional_info = models.TextField(blank=True)
    servings = models.CharField(max_length=200, blank=True)
    rating = models.PositiveSmallIntegerField(default=0)
    on_favorites = models.BooleanField(default=False)
    categories = models.ManyToManyField('core.Category', related_name='recipes', blank=True)
    in_trash = models.BooleanField(default=False, help_text='True if recipe was deleted in Paprika app')

    # TODO: add other fields (ingreds, directions, rating, source, categories, etc... anything that can change and should be flagged in a NewsItem)
    # TODO: add a 'deleted' flag?

    FIELDS_TO_HASH = {'photo_hash', 'name', 'ingredients', 'source', 'total_time', 'cook_time', 'prep_time', 'description', 'source_url', 'difficulty', 'directions', 'notes', 'nutritional_info', 'servings', 'rating'}
    # photo_url ignored because photo_hash indicates whether the photos are different
    FIELDS_TO_DIFF = {'photo_hash', 'name', 'ingredients', 'source', 'total_time', 'cook_time', 'prep_time', 'description', 'source_url', 'difficulty', 'directions', 'notes', 'nutritional_info', 'servings', 'rating', 'categories'}

    def compute_import_stable_hash(self):
        'Hash that is stable, even if a recipe is imported from another account'
        hash = hashlib.sha1()
        for field in sorted(Recipe._meta.get_fields(), key=lambda f: f.name):
            if field.name in Recipe.FIELDS_TO_HASH:
                # Not hashing categories because it's more difficult to add new
                # Recipes because the relationship requires an ID (categories
                # are associated after the Recipe is saved). Also, it may not
                # be worth flagging differences in categorization, because
                # users may have different personal organization schemes.
                # if field.one_to_many or field.many_to_many:
                #     value_list = getattr(self, field.name).values_list('name', flat=True)
                #     value = ','.join(value_list)
                #     add = value.encode()
                #     hash.update(add)
                # else:
                    value = getattr(self, field.name)
                    add = str(value).encode()
                    hash.update(add)
        return hash.hexdigest()

    def get_photo_content(self):
        with open(self.get_photo_filepath(), 'rb') as f:
            return f.read()

    def get_photo_filename(self):
        return urlparse(self.photo_url).path.split('/')[-1]

    def get_photo_filepath(self):
        return os.path.join(settings.MEDIA_ROOT, self.get_photo_filename())

    def get_photo_url(self):
        return os.path.join(settings.MEDIA_URL, self.get_photo_filename())

    def download_photo(self, use_db_url=False):
        if use_db_url:
            # If we recently sync'd this recipe, the signature in the database
            # url should still be valid
            url = self.photo_url
        else:
            # Otherwise, get newly-signed photo url from API
            api_recipe_detail = self.paprika_account.get_recipe(self.uid)
            url = api_recipe_detail['photo_url']

        # Download it to MEDIA folder
        filename = urlparse(url).path.split('/')[-1]
        dest_path = os.path.join(settings.MEDIA_ROOT, filename)
        with requests.get(url, stream=True) as r:
            with open(dest_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        return dest_path


    def diff(self, other):
        'Diffs 2 Recipes, returning {field_name: True, ...} containing all fields changed'
        fields_changed = {}
        for field in Recipe._meta.get_fields():
            if field.name in Recipe.FIELDS_TO_DIFF:
                if field.one_to_many or field.many_to_many:
                    self_list = list(getattr(self, field.name).values_list('name', flat=True))
                    other_list = list(getattr(other, field.name).values_list('name', flat=True))
                    if self_list != other_list:
                        fields_changed[field.name] = True
                else:
                    if getattr(self, field.name) != getattr(other, field.name):
                        fields_changed[field.name] = True

        return fields_changed

    def save(self, *args, **kwargs):
        self.import_stable_hash = self.compute_import_stable_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(BaseModel):
    paprika_account = models.ForeignKey('core.PaprikaAccount', related_name='categories', on_delete=models.CASCADE)
    uid = models.CharField(max_length=200, db_index=True)
    name = models.CharField(max_length=1000, db_index=True)
    # Make this a relation?
    parent_uid = models.CharField(max_length=200, db_index=True, blank=True)
    # order_flag = models.IntegerField()  # Not sure what this field is for

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class NewsItem(BaseModel):
    TYPE_NEW_ACCOUNT, TYPE_RECIPE_ADDED, TYPE_RECIPE_EDITED, TYPE_RECIPE_RATED, TYPE_RECIPE_DELETED = 'new_account', 'recipe_added', 'recipe_edited', 'recipe_rated', 'recipe_deleted'
    TYPE_CHOICES = (
        (TYPE_NEW_ACCOUNT, TYPE_NEW_ACCOUNT),
        (TYPE_RECIPE_ADDED, TYPE_RECIPE_ADDED),
        (TYPE_RECIPE_EDITED, TYPE_RECIPE_EDITED),
        (TYPE_RECIPE_RATED, TYPE_RECIPE_RATED),
        (TYPE_RECIPE_DELETED, TYPE_RECIPE_DELETED),
    )
    TYPE_CHOICES_LIST = (TYPE_NEW_ACCOUNT, TYPE_RECIPE_ADDED, TYPE_RECIPE_EDITED, TYPE_RECIPE_RATED, TYPE_RECIPE_DELETED)
    paprika_account = models.ForeignKey('core.PaprikaAccount', related_name='+', on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    payload = JSONField(default=dict, help_text='Specifies details (e.g. what fields of a recipe were updated)')
    recipe = models.ForeignKey('core.Recipe', null=True, blank=True, related_name='+', on_delete=models.CASCADE, help_text='Related recipe (e.g. if type is added, edited, rated, deleted)')
    previous_recipe = models.ForeignKey('core.Recipe', null=True, blank=True, related_name='+', on_delete=models.CASCADE, help_text='Previous version of the recipe')

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return '{} by {}'.format(self.type, self.paprika_account)
