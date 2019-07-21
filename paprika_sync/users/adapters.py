from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpRequest


class AccountAdapter(DefaultAccountAdapter):

    def is_open_for_signup(self, request: HttpRequest):
        allow_registration = getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
        if not allow_registration:
            invite_token = getattr(settings, "REGISTRATION_INVITE_TOKEN", None)
            if invite_token and request.GET.get('invite') == invite_token:
                return True
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
