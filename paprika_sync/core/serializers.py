from rest_framework import serializers

from .models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'
        # TODO: add exclude for date_ended
        extra_kwargs = {
            'image_url': {'allow_null': True},
        }
