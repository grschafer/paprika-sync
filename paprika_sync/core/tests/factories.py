from typing import Any, Sequence

from factory import DjangoModelFactory, SubFactory, Faker, post_generation

from paprika_sync.core.models import PaprikaAccount
from paprika_sync.users.tests.factories import UserFactory


class PaprikaAccountFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    username = Faker("user_name")
    alias = Faker("name")
    password = Faker("password", length=42)

    class Meta:
        model = PaprikaAccount
        django_get_or_create = ["username"]
