import json

from factory import DjangoModelFactory, SubFactory, Faker

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


def get_test_recipe_dict(overrides=None, del_keys=None):
    recipe_json = '''{"rating":0,"photo_hash":"1b1463bf23e12e0c3b3baa4a6a1ca740db84cd355f500dc42947798119b918a3","on_favorites":false,"photo":"860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg","uid":"84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC0E","scale":null,"ingredients":"45 g Butter, plus extra for coating ramekins\n98 g Sugar, granulated, divided, plus extra for coating ramekins\n34 g Bread flour","is_pinned":null,"source":"Chefsteps.com","total_time":null,"hash":"8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40449","description":null,"source_url":"https://www.chefsteps.com/activities/black-pepper-souffle","difficulty":"","on_grocery_list":null,"in_trash":null,"directions":"A few things to keep in mind before you start.\n\nDo X, then Y, then Z.","categories":[],"photo_url":"http://uploads.paprikaapp.com.s3.amazonaws.com/326504/860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg?Signature=JaDRirnJ%2F6CAUDovP596bfzW7q0%3D&Expires=1550511786&AWSAccessKeyId=AKIAJA4A42FBJBMX5ARA","cook_time":"45 min","name":"Black Pepper Soufflé","created":"2018-10-13 17:31:31","notes":"NOTE: If you’ve got ’em, use ramekins that have smooth, straight interiors.","photo_large":null,"image_url":"https://d3awvtnmmsvyot.cloudfront.net/api/file/Ip0MOte2TdWlXELNtiKD/convert?fit=max&w=2000&quality=60&cache=true&rotate=exif&compress=true","prep_time":"","servings":"3 souffles (140 g each)","nutritional_info":""}'''
    recipe = json.loads(recipe_json, strict=False)
    if del_keys:
        for k in del_keys:
            del recipe[k]
    if overrides:
        recipe.update(overrides)
    return recipe


def get_test_recipes_dict():
    recipes_json = '''[{"uid":"84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC0E","hash":"8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40449"}]'''
    recipes = json.loads(recipes_json, strict=False)
    return recipes
