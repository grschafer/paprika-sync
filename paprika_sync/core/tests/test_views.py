from unittest import mock

import pytest

from django.urls import reverse
from django.test import override_settings

from paprika_sync.core.tests.factories import get_test_recipe_dict, get_test_recipes_dict

pytestmark = pytest.mark.django_db


def test_login_redirect_to_add_paprika_account_if_no_paprika_accounts_associated(verified_user, client):
    # Have to use verified_user so that we actually login, instead of being prompted to confirm our email address
    verified_user.set_password('testpassword')
    verified_user.save()
    response = client.post(reverse('account_login'), {'login': verified_user.username, 'password': 'testpassword'}, follow=True)
    assert response.wsgi_request.path == reverse('core:add_paprika_account')
    assert response.redirect_chain
    assert response.redirect_chain[0][0] == reverse('users:redirect')


@mock.patch('paprika_sync.core.actions.get_recipes', return_value=get_test_recipes_dict())
@mock.patch('paprika_sync.core.actions.get_recipe', return_value=get_test_recipe_dict())
@override_settings(RECIPE_THRESHOLD_TO_DEFER_IMPORT=0)
def test_paprika_account_import_deferred_message(mock_recipe, mock_recipes, user_client):
    response = user_client.post(reverse('core:add_paprika_account'), {'username': 'un', 'password': 'pw', 'alias': 'myname'}, follow=True)
    assert 'Your account contains many recipes! Importing will occur in the background' in response.content.decode('utf-8')
