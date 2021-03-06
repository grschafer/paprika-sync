import pytest

from paprika_sync.core.serializers import RecipeSerializer
from paprika_sync.core.tests.factories import PaprikaAccountFactory, get_test_recipe_dict, CategoryFactory, get_test_categories_dict

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


def test_serializer_photo_url_strips_querystring():
    pa = PaprikaAccountFactory()
    recipe = get_test_recipe_dict(overrides={'paprika_account': pa.id, 'categories': []})
    rs = RecipeSerializer(data=recipe)
    assert rs.is_valid(), rs.errors
    assert '?' not in rs.validated_data['photo_url']


def test_serializer_null_description_ok():
    pa = PaprikaAccountFactory()
    recipe = get_test_recipe_dict(overrides={'paprika_account': pa.id, 'categories': [], 'description': None})
    rs = RecipeSerializer(data=recipe)
    assert rs.is_valid(), rs.errors


def test_serializer_supports_mixed_valid_and_bad_categories():
    pa = PaprikaAccountFactory()
    cat = CategoryFactory(**get_test_categories_dict()[0], paprika_account=pa)
    recipe = get_test_recipe_dict(overrides={'paprika_account': pa.id})
    recipe['categories'].append('not-a-real-category')
    rs = RecipeSerializer(data=recipe)
    assert rs.is_valid(), rs.errors
    rs.save()
    assert rs.instance.categories.get() == cat
