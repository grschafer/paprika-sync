from unittest import mock

import pytest
import requests.exceptions

from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_login_redirect_to_add_paprika_account_if_no_paprika_accounts_associated(verified_user, client):
    # Have to use verified_user so that we actually login, instead of being prompted to confirm our email address
    verified_user.set_password('testpassword')
    verified_user.save()
    response = client.post(reverse('account_login'), {'login': verified_user.username, 'password': 'testpassword'}, follow=True)
    assert response.wsgi_request.path == reverse('core:add_paprika_account')
    assert response.redirect_chain
    assert response.redirect_chain[0][0] == reverse('users:redirect')
