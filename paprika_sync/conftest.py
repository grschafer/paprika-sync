import pytest
from django.conf import settings
from django.test import RequestFactory, Client

from allauth.account.models import EmailAddress

from paprika_sync.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> settings.AUTH_USER_MODEL:
    return UserFactory()


@pytest.fixture
def verified_user(user) -> settings.AUTH_USER_MODEL:
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    return user


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def user_client(user, client):
    client.force_login(user)
    return client


@pytest.fixture
def verified_user_client(verified_user, client):
    client.force_login(verified_user)
    return client
