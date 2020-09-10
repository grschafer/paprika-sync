from unittest import mock
from uuid import uuid4

import django_fsm
import pytest

from paprika_sync.core.models import PaprikaAccount, Recipe, NewsItem, Category
from paprika_sync.core.tests.factories import get_test_recipe_dict, get_test_recipes_dict, recipe_to_api_dict, recipes_to_api_dict, PaprikaAccountFactory, RecipeFactory, get_test_categories_dict

pytestmark = pytest.mark.django_db


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=get_test_recipes_dict())
@mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=get_test_recipe_dict())
@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_import_account(mock_recipe, mock_recipes, mock_categories, user):
    PaprikaAccount.import_account(user, 'user', 'pass', 'alias')
    pa = PaprikaAccount.objects.get()
    assert pa.user == user
    assert pa.username == 'user'
    assert pa.password == 'pass'
    assert pa.alias == 'alias'
    mock_recipes.assert_called_once()
    r = pa.recipes.get()
    assert r.name == 'Prosecutor'
    mock_recipe.assert_called_once()


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=get_test_recipes_dict())
@mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=get_test_recipe_dict())
@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_repeated_import_not_allowed(mock_recipe, mock_recipes, mock_categories, user):
    PaprikaAccount.import_account(user, 'user', 'pass', 'alias')
    assert Recipe.objects.all().count() == 1
    pa = PaprikaAccount.objects.get()
    recipes = get_test_recipes_dict()
    with pytest.raises(django_fsm.TransitionNotAllowed):
        pa.start_import_recipes()
        pa.import_recipes(recipes)
    assert Recipe.objects.all().count() == 1


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_account_recipes_from_api_no_change(mock_categories, user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory(paprika_account=pa)

    recipes_api_dict = recipes_to_api_dict(pa.recipes.all())
    recipe_api_dict = recipe_to_api_dict(r1)
    pa.start_sync_recipes()
    with mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=recipe_api_dict):
        pa.sync_recipes()

    assert Recipe.objects.all().count() == 1
    assert NewsItem.objects.all().count() == 0


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_account_recipes_from_api_recipe_added(mock_categories, user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory(paprika_account=pa)
    r2 = RecipeFactory.build(paprika_account=None)

    recipes_api_dict = recipes_to_api_dict([r1, r2])
    recipe_api_dict = recipe_to_api_dict(r2)
    pa.start_sync_recipes()
    with mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=recipe_api_dict):
        pa.sync_recipes()

    assert Recipe.objects.all().count() == 2
    assert Recipe.objects.filter(date_ended__isnull=True).count() == 2
    assert NewsItem.objects.all().count() == 1
    assert NewsItem.objects.get().type == NewsItem.TYPE_RECIPE_ADDED


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_account_recipes_from_api_recipe_edited(mock_categories, user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory(paprika_account=pa)
    new_name = 'New name'
    r1.name = new_name
    r1.hash = str(uuid4())

    recipes_api_dict = recipes_to_api_dict([r1])
    recipe_api_dict = recipe_to_api_dict(r1)
    pa.start_sync_recipes()
    with mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=recipe_api_dict):
        pa.sync_recipes()

    assert Recipe.objects.all().count() == 2
    r1, r2 = Recipe.objects.all().order_by('id')
    assert r1.date_ended
    assert r2.date_ended is None
    assert r1.uid == r2.uid
    assert r1.name != r2.name
    assert r2.name == new_name
    assert NewsItem.objects.all().count() == 1
    ni = NewsItem.objects.get()
    assert ni.type == NewsItem.TYPE_RECIPE_EDITED
    assert set(ni.payload['fields_changed']) == {'name'}
    assert ni.payload['recipe'] == r2.id
    assert ni.payload['previous_recipe'] == r1.id


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_account_recipes_from_api_recipe_edited_rating_only(mock_categories, user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory(paprika_account=pa, rating=0)
    new_rating = 5
    r1.rating = new_rating
    r1.hash = str(uuid4())

    recipes_api_dict = recipes_to_api_dict([r1])
    recipe_api_dict = recipe_to_api_dict(r1)
    pa.start_sync_recipes()
    with mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=recipe_api_dict):
        pa.sync_recipes()

    r1, r2 = Recipe.objects.all().order_by('id')
    assert NewsItem.objects.all().count() == 1
    ni = NewsItem.objects.get()
    assert ni.type == NewsItem.TYPE_RECIPE_RATED
    assert r1.rating == 0
    assert r2.rating == new_rating


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_account_recipes_from_api_recipe_edited_rating_and_other_fields(mock_categories, user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory(paprika_account=pa, rating=0)
    new_rating = 5
    new_notes = 'These notes are different'
    r1.rating = new_rating
    r1.notes = new_notes
    r1.hash = str(uuid4())

    recipes_api_dict = recipes_to_api_dict([r1])
    recipe_api_dict = recipe_to_api_dict(r1)
    pa.start_sync_recipes()
    with mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=recipe_api_dict):
        pa.sync_recipes()

    r1, r2 = Recipe.objects.all().order_by('id')
    assert NewsItem.objects.all().count() == 2
    ni1, ni2 = NewsItem.objects.all().order_by('id')
    assert ni1.type == NewsItem.TYPE_RECIPE_RATED
    assert ni2.type == NewsItem.TYPE_RECIPE_EDITED
    assert ni2.payload['fields_changed'] == ['notes']


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_account_recipes_from_api_recipe_deleted(mock_categories, user):
    pa = PaprikaAccountFactory()
    RecipeFactory(paprika_account=pa)

    recipes_api_dict = recipes_to_api_dict([])
    pa.start_sync_recipes()
    with mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=recipes_api_dict):
        pa.sync_recipes()

    assert Recipe.objects.all().count() == 1
    assert Recipe.objects.get().date_ended is not None
    assert NewsItem.objects.all().count() == 1
    assert NewsItem.objects.get().type == NewsItem.TYPE_RECIPE_DELETED


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_account_recipes_from_api_recipe_trashed(mock_categories, user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory(paprika_account=pa)
    r1.in_trash = True
    r1.hash = str(uuid4())

    recipes_api_dict = recipes_to_api_dict([r1])
    recipe_api_dict = recipe_to_api_dict(r1)
    pa.start_sync_recipes()
    with mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=recipe_api_dict):
        pa.sync_recipes()

    assert Recipe.objects.all().count() == 2
    assert Recipe.objects.earliest('id').date_ended is not None
    assert not Recipe.objects.earliest('id').in_trash
    assert Recipe.objects.latest('id').date_ended is None
    assert Recipe.objects.latest('id').in_trash
    assert NewsItem.objects.all().count() == 1
    assert NewsItem.objects.get().type == NewsItem.TYPE_RECIPE_DELETED


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_account_recipes_from_api_dont_notify_added_trashed_recipe(mock_categories, user):
    pa = PaprikaAccountFactory()
    r1 = RecipeFactory.build(paprika_account=None, in_trash=True)

    recipes_api_dict = recipes_to_api_dict([r1])
    recipe_api_dict = recipe_to_api_dict(r1)
    pa.start_sync_recipes()
    with mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipes', return_value=recipes_api_dict), mock.patch('paprika_sync.core.models.PaprikaAccount.get_recipe', return_value=recipe_api_dict):
        pa.sync_recipes()

    assert Recipe.objects.all().count() == 1
    assert Recipe.objects.get().in_trash
    assert NewsItem.objects.all().count() == 0


@mock.patch('paprika_sync.core.models.PaprikaAccount.get_categories', return_value=get_test_categories_dict())
def test_sync_categories(mock_categories, user):
    pa = PaprikaAccountFactory()
    assert Category.objects.all().count() == 0
    pa.sync_categories()
    assert Category.objects.all().count() == 1
    pa.sync_categories()
    assert Category.objects.all().count() == 1


@mock.patch('paprika_sync.core.models.PaprikaAccount.clone_recipe', return_value=None)
def test_clone_recipe():
    # No real backend activity from this action, so not much to test
    pass
