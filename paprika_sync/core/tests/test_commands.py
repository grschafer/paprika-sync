from unittest import mock
from uuid import uuid4

import pytest

from django.core.management import call_command
from django.utils import timezone

from paprika_sync.core.models import PaprikaAccount, Recipe, NewsItem
from paprika_sync.core.tests.factories import PaprikaAccountFactory, get_test_recipe_dict, get_test_recipes_dict, recipes_to_api_dict, RecipeFactory, get_test_categories_dict, recipe_to_api_dict

pytestmark = pytest.mark.django_db


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=get_test_recipes_dict())
@mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=get_test_recipe_dict())
@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_import_new_account_recipes(mock_recipe, mock_recipes, mock_categories, user):
    pa = PaprikaAccountFactory(import_sync_status=PaprikaAccount.IMPORT_DEFERRED)
    assert Recipe.objects.all().count() == 0
    call_command('import_new_account_recipes')
    assert Recipe.objects.all().count() == 1
    pa = PaprikaAccount.objects.get(id=pa.id)
    assert pa.import_sync_status == PaprikaAccount.SYNC_SUCCESS


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_recipes_from_api(mock_categories, user):
    pa = PaprikaAccountFactory(import_sync_status=PaprikaAccount.SYNC_SUCCESS, last_synced=timezone.now() - timezone.timedelta(days=2))
    r1 = RecipeFactory(paprika_account=pa)  # NOQA
    r2 = RecipeFactory(paprika_account=pa)
    r3 = RecipeFactory.build(paprika_account=None)
    r2.name = 'New name'
    r2.hash = str(uuid4())
    recipes_api_dict = recipes_to_api_dict([r2, r3])

    assert Recipe.objects.all().count() == 2
    with mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=recipes_api_dict), \
            mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', side_effect=[recipe_to_api_dict(r2), recipe_to_api_dict(r3)]):
        call_command('sync_recipes_from_api')
    assert Recipe.objects.all().count() == 4
    # r1 deleted, r2 edited (renamed), r3 added
    assert NewsItem.objects.all().count() == 3
