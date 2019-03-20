from factory import DjangoModelFactory, SubFactory, Faker

from paprika_sync.core.models import PaprikaAccount, Recipe
from paprika_sync.users.tests.factories import UserFactory


class PaprikaAccountFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    username = Faker("user_name")
    alias = Faker("name")
    password = Faker("password", length=42)
    import_status = PaprikaAccount.IMPORT_SUCCESS

    class Meta:
        model = PaprikaAccount
        django_get_or_create = ["username"]


class RecipeFactory(DjangoModelFactory):
    paprika_account = SubFactory(PaprikaAccountFactory)
    uid = Faker('uuid4')
    hash = Faker('uuid4')
    photo_hash = Faker('uuid4')
    name = Faker('name')
    image_url = Faker('url')

    class Meta:
        model = Recipe


def get_test_recipe_dict(uid=None, overrides=None, del_keys=None):
    recipes = [
        {"rating": 0, "photo_hash": "1b1463bf23e12e0c3b3baa4a6a1ca740db84cd355f500dc42947798119b918a3", "on_favorites": False, "photo": "860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg", "uid": "84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC00", "scale": None, "ingredients": "45 g Butter, plus extra for coating ramekins\n98 g Sugar, granulated, divided, plus extra for coating ramekins\n34 g Bread flour", "is_pinned": None, "source": "Chefsteps.com", "total_time": None, "hash": "8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40449", "description": None, "source_url": "https://www.chefsteps.com/activities/black-pepper-souffle", "difficulty": "", "on_grocery_list": None, "in_trash": None, "directions": "A few things to keep in mind before you start.\n\nDo X, then Y, then Z.", "categories": [], "photo_url": "http://uploads.paprikaapp.com.s3.amazonaws.com/326504/860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg?Signature=JaDRirnJ%2F6CAUDovP596bfzW7q0%3D&Expires=1550511786&AWSAccessKeyId=AKIAJA4A42FBJBMX5ARA", "cook_time": "45 min", "name": "Test Recipe 0", "created": "2018-10-13 17: 31: 31", "notes": "NOTE:  If you’ve got ’em, use ramekins that have smooth, straight interiors.", "photo_large": None, "image_url": "https://d3awvtnmmsvyot.cloudfront.net/api/file/Ip0MOte2TdWlXELNtiKD/convert?fit=max&w=2000&quality=60&cache=true&rotate=exif&compress=true", "prep_time": "", "servings": "3 souffles (140 g each)", "nutritional_info": ""},
        {"rating": 0, "photo_hash": "1b1463bf23e12e0c3b3baa4a6a1ca740db84cd355f500dc42947798119b918a3", "on_favorites": False, "photo": "860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg", "uid": "84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC01", "scale": None, "ingredients": "45 g Butter", "is_pinned": None, "source": "Chefsteps.com", "total_time": None, "hash": "8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40449", "description": None, "source_url": "", "difficulty": "", "on_grocery_list": None, "in_trash": None, "directions": "Blahblah", "categories": [], "photo_url": "http://uploads.paprikaapp.com.s3.amazonaws.com/326504/860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg?Signature=JaDRirnJ%2F6CAUDovP596bfzW7q0%3D&Expires=1550511786&AWSAccessKeyId=AKIAJA4A42FBJBMX5ARA", "cook_time": "45 min", "name": "Test Recipe 1", "created": "2018-10-13 17: 31: 31", "notes": "", "photo_large": None, "image_url": "https://d3awvtnmmsvyot.cloudfront.net/api/file/Ip0MOte2TdWlXELNtiKD/convert?fit=max&w=2000&quality=60&cache=true&rotate=exif&compress=true", "prep_time": "", "servings": "3 souffles (140 g each)", "nutritional_info": ""},
        {"rating": 0, "photo_hash": "1b1463bf23e12e0c3b3baa4a6a1ca740db84cd355f500dc42947798119b918a3", "on_favorites": False, "photo": "860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg", "uid": "84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC02", "scale": None, "ingredients": "45 g Butter", "is_pinned": None, "source": "Chefsteps.com", "total_time": None, "hash": "8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40449", "description": None, "source_url": "", "difficulty": "", "on_grocery_list": None, "in_trash": None, "directions": "Blahblah", "categories": [], "photo_url": "http://uploads.paprikaapp.com.s3.amazonaws.com/326504/860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg?Signature=JaDRirnJ%2F6CAUDovP596bfzW7q0%3D&Expires=1550511786&AWSAccessKeyId=AKIAJA4A42FBJBMX5ARA", "cook_time": "45 min", "name": "Test Recipe 2", "created": "2018-10-13 17: 31: 31", "notes": "", "photo_large": None, "image_url": "https://d3awvtnmmsvyot.cloudfront.net/api/file/Ip0MOte2TdWlXELNtiKD/convert?fit=max&w=2000&quality=60&cache=true&rotate=exif&compress=true", "prep_time": "", "servings": "3 souffles (140 g each)", "nutritional_info": ""},
    ]
    if uid:
        recipe = [r for r in recipes if r['uid'] == uid][0]
    else:
        recipe = recipes[0]

    if del_keys:
        for k in del_keys:
            del recipe[k]
    if overrides:
        recipe.update(overrides)
    return recipe


def get_test_recipes_dict(qty=1):
    recipes = [
        {"uid": "84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC00", "hash": "8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40440"},
        {"uid": "84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC01", "hash": "8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40441"},
        {"uid": "84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC02", "hash": "8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40442"},
    ]
    return recipes[:qty]


def recipe_to_api_dict(recipe):
    return {
        'photo_hash': recipe.photo_hash,
        'uid': recipe.uid,
        'hash': recipe.hash,
        'name': recipe.name,
        'image_url': recipe.image_url,
        # TODO: add other fields?
    }


def recipes_to_api_dict(recipes):
    return [
        {'uid': r.uid, 'hash': r.hash} for r in recipes
    ]
