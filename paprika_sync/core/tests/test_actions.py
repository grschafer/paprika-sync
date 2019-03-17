from unittest import mock

import pytest

from paprika_sync.core.actions import import_account, import_recipes
from paprika_sync.core.models import PaprikaAccount, Recipe
from paprika_sync.core.tests.factories import get_test_recipe_dict, get_test_recipes_dict

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
    assert r.name == 'Black Pepper Soufflé'
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
