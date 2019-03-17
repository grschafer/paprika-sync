from unittest import mock

import pytest

from django.core.management import call_command

from paprika_sync.core.models import PaprikaAccount, Recipe
from paprika_sync.core.tests.factories import PaprikaAccountFactory, get_test_recipe_dict, get_test_recipes_dict

pytestmark = pytest.mark.django_db


@mock.patch('paprika_sync.core.management.commands.import_new_account_recipes.get_recipes', return_value=get_test_recipes_dict())
@mock.patch('paprika_sync.core.actions.get_recipe', return_value=get_test_recipe_dict())
def test_import_account(mock_recipe, mock_recipes, user):
    pa = PaprikaAccountFactory(import_status=PaprikaAccount.IMPORT_DEFERRED)
    assert Recipe.objects.all().count() == 0
    call_command('import_new_account_recipes')
    assert Recipe.objects.all().count() == 1
    pa.refresh_from_db()
    assert pa.import_status == PaprikaAccount.IMPORT_SUCCESS
