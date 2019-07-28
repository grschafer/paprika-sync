from django.utils import timezone

import factory
from factory import DjangoModelFactory, SubFactory, Faker

from paprika_sync.core.models import PaprikaAccount, Recipe, Category
from paprika_sync.users.tests.factories import UserFactory


class PaprikaAccountFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    username = Faker("email")
    alias = Faker("name")
    password = Faker("password", length=42)
    import_sync_status = PaprikaAccount.SYNC_SUCCESS
    last_synced = timezone.now()
    sync_failure_count = 0

    class Meta:
        model = PaprikaAccount
        django_get_or_create = ["username"]


class CategoryFactory(DjangoModelFactory):
    paprika_account = SubFactory(PaprikaAccountFactory)
    uid = Faker('uuid4')
    name = Faker('name')
    parent_uid = Faker('uuid4')

    class Meta:
        model = Category


class RecipeFactory(DjangoModelFactory):
    paprika_account = SubFactory(PaprikaAccountFactory)
    # categories = SubFactory(CategoryFactory)
    uid = Faker('uuid4')
    date_ended = None
    hash = Faker('uuid4')
    photo_hash = Faker('uuid4')
    name = Faker('name')
    photo_url = Faker('uri')
    ingredients = Faker('paragraph')
    source = Faker('company')
    total_time = Faker('sentence')
    cook_time = Faker('sentence')
    prep_time = Faker('sentence')
    created = Faker('date_time')
    description = Faker('paragraph')
    source_url = Faker('uri')
    difficulty = Faker('word')
    directions = Faker('paragraph')
    notes = Faker('paragraph')
    nutritional_info = Faker('paragraph')
    servings = Faker('word')
    rating = Faker('pyint', min=0, max=5)
    on_favorites = Faker('pybool')
    in_trash = False

    class Meta:
        model = Recipe

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of categories were passed in, use them
            for category in extracted:
                self.categories.add(category)
        else:
            self.categories.add(CategoryFactory(paprika_account=self.paprika_account))


def get_test_recipe_dict(overrides=None, del_keys=None):
    recipe = {
        "rating": 3,
        "photo_hash": None,
        "on_favorites": False,
        "photo": None,
        "uid": "11AA6F09-85D3-4FD8-B36E-03B97E6FD2A4",
        "scale": None,
        "ingredients": "Mixed Drink Recipe from Cocktail Builder\n1 1/2 oz of rye\n1/2 oz of Herbal Liqueur\n1/2 oz of St Germain\n1/2 oz of Lemon Juice",
        "is_pinned": False,
        "source": "Cocktailbuilder.com",
        "total_time": "",
        "hash": "7774BBFE21FF4162016C7E5223F1EEE175F8825416270780402471357FE6A264",
        "description": "",
        "source_url": "https://www.cocktailbuilder.com/recipe/prosecutor",
        "difficulty": "",
        "on_grocery_list": None,
        "in_trash": False,
        "directions": "Shake, chilled single rocks glass, no garnish.",
        "categories": ["90A5A11B-204A-40BC-AEB0-E7849CB5C043"],
        "photo_url": 'http://uploads.paprikaapp.com.s3.amazonaws.com/117337/0972A167-C41F-44D0-8C5A-7FEB109FDB7A-915-000000FD7616CB77.jpg?Signature=21mKNUap6q6HOxUQSw94d2yrR3o%3D&Expires=1563838240&AWSAccessKeyId=AKIAJA4A42FBJBMX5ARA',
        "cook_time": "2 min",
        "name": "Prosecutor",
        "created": "2019-06-16 22:32:01",
        "notes": "Halve the fernet and reduce lemon juice a bit",
        "photo_large": None,
        "image_url": None,
        "prep_time": "5 min",
        "servings": "",
        "nutritional_info": "",
    }
    if del_keys:
        for k in del_keys:
            del recipe[k]
    if overrides:
        recipe.update(overrides)
    return recipe


def get_test_recipes_dict(qty=1):
    recipes = [
        {
            "uid": "84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC00",
            "hash": "8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40440",
        },
        {
            "uid": "84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC01",
            "hash": "8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40441",
        },
        {
            "uid": "84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC02",
            "hash": "8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40442",
        },
    ]
    return recipes[:qty]


def recipe_to_api_dict(recipe):
    return {
        'uid': recipe.uid,
        'date_ended': recipe.date_ended,
        'hash': recipe.hash,
        'photo_hash': recipe.photo_hash,
        'name': recipe.name,
        'photo_url': recipe.photo_url,
        'ingredients': recipe.ingredients,
        'source': recipe.source,
        'total_time': recipe.total_time,
        'cook_time': recipe.cook_time,
        'prep_time': recipe.prep_time,
        'created': recipe.created,
        'description': recipe.description,
        'source_url': recipe.source_url,
        'difficulty': recipe.difficulty,
        'directions': recipe.directions,
        'notes': recipe.notes,
        'nutritional_info': recipe.nutritional_info,
        'servings': recipe.servings,
        'rating': recipe.rating,
        'on_favorites': recipe.on_favorites,
        'categories': [cat.uid for cat in recipe.categories.all()] if recipe.id else [],
        'in_trash': recipe.in_trash,
    }


def recipes_to_api_dict(recipes):
    return [{'uid': r.uid, 'hash': r.hash} for r in recipes]


def get_test_categories_dict(qty=1):
    categories = [
        {
            # 'order_flag': 37,
            'uid': '90A5A11B-204A-40BC-AEB0-E7849CB5C043',
            'parent_uid': '',
            'name': 'Drink',
        }
    ]
    return categories[:qty]
