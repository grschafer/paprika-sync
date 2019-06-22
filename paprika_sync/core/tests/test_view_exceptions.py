from unittest import mock

import pytest
import requests.exceptions

from django.urls import reverse

pytestmark = pytest.mark.django_db


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', side_effect=requests.exceptions.ConnectionError)
def test_import_account_connectionerror_populates_messages(mock_recipes, user_client):
    response = user_client.post(reverse('core:add_paprika_account'), {'username': 'un', 'password': 'pw', 'alias': 'myname'}, follow=True)
    assert response.wsgi_request.path == reverse('core:add_paprika_account')
    assert 'Error importing account' in response.content.decode('utf-8')
