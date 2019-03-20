from unittest import mock
from uuid import uuid4

import pytest

from paprika_sync.core.actions import import_account, import_recipes, sync_account_recipes_from_api
from paprika_sync.core.models import PaprikaAccount, Recipe, NewsItem
from paprika_sync.core.tests.factories import get_test_recipe_dict, get_test_recipes_dict, recipe_to_api_dict, recipes_to_api_dict, PaprikaAccountFactory, RecipeFactory

pytestmark = pytest.mark.django_db


@mock.patch('paprika_sync.core.actions.get_recipes', return_value=get_test_recipes_dict())
@mock.patch('paprika_sync.core.actions.get_recipe', return_value=get_test_recipe_dict())
def test_import_account(mock_recipe, mock_recipes, user):
    import_account(user, 'user', 'pass', 'alias')
    pa = PaprikaAccount.objects.get()
    assert pa.user == user
    assert pa.username == 'user'
    assert pa.password == 'pass'
    assert pa.alias == 'alias'
    mock_recipes.assert_called_once()
    r = pa.recipes.get()
    assert r.name == 'Test Recipe 0'
    mock_recipe.assert_called_once()


@mock.patch('paprika_sync.core.actions.get_recipes', return_value=get_test_recipes_dict())
@mock.patch('paprika_sync.core.actions.get_recipe', return_value=get_test_recipe_dict())
def test_repeated_import_doesnt_duplicate_recipes(mock_recipe, mock_recipes, user):
    import_account(user, 'user', 'pass', 'alias')
    assert Recipe.objects.all().count() == 1
    pa = PaprikaAccount.objects.get()
    recipes = get_test_recipes_dict()
    import_recipes(pa, recipes)
    assert Recipe.objects.all().count() == 1


def test_sync_account_recipes_from_api_no_change(user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory(paprika_account=pa)

    recipes_api_dict = recipes_to_api_dict(pa.recipes.all())
    recipe_api_dict = recipe_to_api_dict(r1)
    with mock.patch('paprika_sync.core.actions.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.actions.get_recipe', return_value=recipe_api_dict):
        sync_account_recipes_from_api(pa)

    assert Recipe.objects.all().count() == 1
    assert NewsItem.objects.all().count() == 0


def test_sync_account_recipes_from_api_recipe_added(user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory(paprika_account=pa)
    r2 = RecipeFactory.build(paprika_account=None)

    recipes_api_dict = recipes_to_api_dict([r1, r2])
    recipe_api_dict = recipe_to_api_dict(r2)
    with mock.patch('paprika_sync.core.actions.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.actions.get_recipe', return_value=recipe_api_dict):
        sync_account_recipes_from_api(pa)

    assert Recipe.objects.all().count() == 2
    assert Recipe.objects.filter(date_ended__isnull=True).count() == 2
    assert NewsItem.objects.all().count() == 1
    assert NewsItem.objects.get().type == NewsItem.TYPE_RECIPE_ADDED


def test_sync_account_recipes_from_api_recipe_edited(user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory(paprika_account=pa)
    new_name = 'New name'
    r1.name = new_name
    r1.hash = str(uuid4())

    recipes_api_dict = recipes_to_api_dict([r1])
    recipe_api_dict = recipe_to_api_dict(r1)
    with mock.patch('paprika_sync.core.actions.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.actions.get_recipe', return_value=recipe_api_dict):
        sync_account_recipes_from_api(pa)

    assert Recipe.objects.all().count() == 2
    r1, r2 = Recipe.objects.all().order_by('id')
    assert r1.date_ended
    assert r2.date_ended is None
    assert r1.uid == r2.uid
    assert r1.name != r2.name
    assert r2.name == new_name
    assert NewsItem.objects.all().count() == 1
    ni = NewsItem.objects.get()
    assert ni.type == NewsItem.TYPE_RECIPE_EDITED
    assert set(ni.payload['fields_changed']) == {'name', 'hash'}
    assert ni.payload['recipe'] == r2.id
    assert ni.payload['previous_recipe'] == r1.id


def test_sync_account_recipes_from_api_recipe_deleted(user):
    pa = PaprikaAccountFactory()
    RecipeFactory(paprika_account=pa)

    recipes_api_dict = recipes_to_api_dict([])
    with mock.patch('paprika_sync.core.actions.get_recipes', return_value=recipes_api_dict):
        sync_account_recipes_from_api(pa)

    assert Recipe.objects.all().count() == 1
    assert Recipe.objects.get().date_ended is not None
    assert NewsItem.objects.all().count() == 1
    assert NewsItem.objects.get().type == NewsItem.TYPE_RECIPE_DELETED
