import pytest
from django.conf import settings
from django.test import RequestFactory, override_settings
from django.urls import reverse

from allauth.account.views import SignupView

from paprika_sync.users.views import UserUpdateView

pytestmark = pytest.mark.django_db


class TestUserUpdateView:
    """
    TODO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """

    def test_get_success_url(
        self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
    ):
        view = UserUpdateView()
        request = request_factory.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_success_url() == f"/users/{user.username}/"

    def test_get_object(
        self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
    ):
        view = UserUpdateView()
        request = request_factory.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_object() == user


@override_settings(DJANGO_ACCOUNT_ALLOW_REGISTRATION=False, REGISTRATION_INVITE_TOKEN=None)
def test_registration_without_invite(client):
    url = reverse('account_signup')
    resp = client.get(url)
    assert SignupView.template_name_signup_closed in resp.template_name or SignupView.template_name_signup_closed == resp.template_name


@override_settings(DJANGO_ACCOUNT_ALLOW_REGISTRATION=False, REGISTRATION_INVITE_TOKEN='blah')
def test_registration_with_invite(client):
    url = reverse('account_signup') + '?invite=blah'
    resp = client.get(url)
    assert SignupView.template_name in resp.template_name or SignupView.template_name == resp.template_name


@override_settings(DJANGO_ACCOUNT_ALLOW_REGISTRATION=False, REGISTRATION_INVITE_TOKEN='blah')
def test_registration_with_wrong_invite(client):
    url = reverse('account_signup') + '?invite=wrong'
    resp = client.get(url)
    assert SignupView.template_name_signup_closed in resp.template_name or SignupView.template_name_signup_closed == resp.template_name
