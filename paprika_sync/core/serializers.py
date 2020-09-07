from rest_framework import serializers

from .fields import UidRelatedField
from .models import Category, Recipe
from .utils import strip_query_params, make_s3_url_https


# Handy reference for serializers: http://cdrf.co/


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        extra_kwargs = {
            # These fields may be null in the API, we transform them to empty strings below
            'parent_uid': {'allow_null': True},
        }

    def validate_parent_uid(self, value):
        return '' if value is None else value


class RecipeSerializer(serializers.ModelSerializer):
    # Recipes in Paprika API aren't updated to remove missing/deleted categories, so ignore any categories we don't know about
    categories = UidRelatedField(queryset=Category.objects, many=True, ignore_missing_relation=True)
    NULL_TO_EMPTY_STR_FIELDS = {
        'cook_time',
        'description',
        'difficulty',
        'directions',
        'image_url',
        'in_trash',
        'is_pinned',
        'notes',
        'nutritional_info',
        'on_grocery_list',
        'photo',
        'photo_hash',
        'photo_large',
        'photo_url',
        'prep_time',
        'scale',
        'servings',
        'source_url',
        'total_time',
    }

    class Meta:
        model = Recipe
        fields = '__all__'
        # TODO: add exclude for date_ended?
        extra_kwargs = {
            'in_trash': {'allow_null': True},
        }

    def validate_photo_url(self, value):
        # Strip off query params so image access doesn't expire
        # TODO: Download the url to local server instead of adding load to paprika's s3 account
        # Rearrange url to use https version (s3.amazonaws.com/<bucket> instead of <bucket>.s3.amazonaws.com)
        return make_s3_url_https(strip_query_params(value))

    def to_internal_value(self, data):
        'Convert null fields to empty string as recommended for django db models'
        for key, value in data.items():
            if key in RecipeSerializer.NULL_TO_EMPTY_STR_FIELDS and value is None:
                data[key] = ''
        return super().to_internal_value(data)
