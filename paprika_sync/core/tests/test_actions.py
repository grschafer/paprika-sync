from unittest import mock

import pytest

from paprika_sync.core.actions import import_account
from paprika_sync.core.models import PaprikaAccount
from paprika_sync.core.tests.factories import get_test_recipe_dict, get_test_recipes_dict
from paprika_sync.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@mock.patch('paprika_sync.core.actions.get_recipes', return_value=get_test_recipes_dict())
@mock.patch('paprika_sync.core.actions.get_recipe', return_value=get_test_recipe_dict())
def test_import_account(mock_recipe, mock_recipes):
    u = UserFactory()
    import_account(u, 'user', 'pass', 'alias')
    pa = PaprikaAccount.objects.get()
    assert pa.user == u
    assert pa.username == 'user'
    assert pa.password == 'pass'
    assert pa.alias == 'alias'
    mock_recipes.assert_called_once()
    r = pa.recipes.get()
    assert r.name == 'Black Pepper Soufflé'
    mock_recipe.assert_called_once()
