from rest_framework import serializers

from .models import Category, Recipe


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
    class Meta:
        model = Recipe
        fields = '__all__'
        # TODO: add exclude for date_ended
        extra_kwargs = {
            # These fields may be null in the API, we transform them to empty strings below
            'photo_hash': {'allow_null': True},
            'photo_url': {'allow_null': True},
        }

    def validate_photo_url(self, value):
        if value is None:
            return ''
        # Strip off query params so image access doesn't expire
        # TODO: Download the url to local server instead of adding load to paprika's s3 account
        return value.partition('?')[0]

    def validate_photo_hash(self, value):
        return '' if value is None else value
