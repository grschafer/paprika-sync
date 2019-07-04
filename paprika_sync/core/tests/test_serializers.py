import pytest

from paprika_sync.core.serializers import RecipeSerializer
from paprika_sync.core.tests.factories import PaprikaAccountFactory, get_test_recipe_dict

pytestmark = pytest.mark.django_db


def test_serializer():
    pa = PaprikaAccountFactory()
    recipe = get_test_recipe_dict(overrides={'paprika_account': pa.id, 'categories': []})
    rs = RecipeSerializer(data=recipe)
    assert rs.is_valid(), rs.errors


def test_serializer_null_photo_url_ok():
    pa = PaprikaAccountFactory()
    recipe = get_test_recipe_dict(overrides={'paprika_account': pa.id, 'categories': [], 'photo_url': None})
    rs = RecipeSerializer(data=recipe)
    assert rs.is_valid(), rs.errors
