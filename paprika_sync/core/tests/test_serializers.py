import json
import pytest

from paprika_sync.core.serializers import RecipeSerializer
from paprika_sync.core.tests.factories import PaprikaAccountFactory

pytestmark = pytest.mark.django_db


test_recipe_json = '''{"rating":0,"photo_hash":"1b1463bf23e12e0c3b3baa4a6a1ca740db84cd355f500dc42947798119b918a3","on_favorites":false,"photo":"860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg","uid":"84B62AEC-DB66-48C5-91ED-F9BF8FA76275-2904-000003304F23DC0E","scale":null,"ingredients":"45 g Butter, plus extra for coating ramekins\n98 g Sugar, granulated, divided, plus extra for coating ramekins\n34 g Bread flour","is_pinned":null,"source":"Chefsteps.com","total_time":null,"hash":"8785094ec64a06421d5e229d331bedc84f6c4304b5f8b7cc1663752cd0c40449","description":null,"source_url":"https://www.chefsteps.com/activities/black-pepper-souffle","difficulty":"","on_grocery_list":null,"in_trash":null,"directions":"A few things to keep in mind before you start. First, you can prepare the recipe up to Step 8, when you fill the ramekins with batter, and then reserve them in the fridge for about 30 minutes before baking. This way, you can prep them in advance and then pop ’em in the oven when you’re ready.\n\nSecond, this recipe yields three 140 g soufflés. You may be thinking, “Does this mean you’re encouraging me to have a threesome on Valentine's Day?” No. (Unless that’s your thing.) The recipe yields three soufflés because it’s pretty hard to nail an entire batch of perfectly risen treats. Having a third gives you some wiggle room if one doesn’t rise, and since the ingredients are cheap, you can just chuck the extra if you don’t need it. (Or invite another lover?)","categories":[],"photo_url":"http://uploads.paprikaapp.com.s3.amazonaws.com/326504/860D403B-2D9F-40B9-A8FC-518C24CD8B76-2904-000003304F24FF05.jpg?Signature=JaDRirnJ%2F6CAUDovP596bfzW7q0%3D&Expires=1550511786&AWSAccessKeyId=AKIAJA4A42FBJBMX5ARA","cook_time":"45 min","name":"Black Pepper Soufflé","created":"2018-10-13 17:31:31","notes":"NOTE: If you’ve got ’em, use ramekins that have smooth, straight interiors.","photo_large":null,"image_url":"https://d3awvtnmmsvyot.cloudfront.net/api/file/Ip0MOte2TdWlXELNtiKD/convert?fit=max&w=2000&quality=60&cache=true&rotate=exif&compress=true","prep_time":"","servings":"3 souffles (140 g each)","nutritional_info":""}'''


def test_serializer():
    pa = PaprikaAccountFactory()
    recipe = json.loads(test_recipe_json, strict=False)
    recipe['paprika_account'] = pa.id
    rs = RecipeSerializer(data=recipe)
    assert rs.is_valid(), rs.errors


def test_serializer_null_image_url_ok():
    pa = PaprikaAccountFactory()
    recipe = json.loads(test_recipe_json, strict=False)
    recipe['paprika_account'] = pa.id
    recipe['image_url'] = None
    rs = RecipeSerializer(data=recipe)
    assert rs.is_valid(), rs.errors


def test_serializer_error_on_missing_image_url():
    pa = PaprikaAccountFactory()
    recipe = json.loads(test_recipe_json, strict=False)
    recipe['paprika_account'] = pa.id
    del recipe['image_url']
    rs = RecipeSerializer(data=recipe)
    assert not rs.is_valid()
