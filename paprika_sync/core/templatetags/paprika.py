from django import template
from django.db.models.manager import BaseManager

register = template.Library()


@register.simple_tag
def diff(recipe, other, field, sub_field=None):
    mine = getattr(recipe, field)
    yours = getattr(other, field)
    if isinstance(mine, BaseManager) and sub_field:
        mine = sorted(mine.all().values_list(sub_field, flat=True))
        yours = sorted(yours.all().values_list(sub_field, flat=True))

    if mine != yours:
        return 'different'
    return ''


@register.simple_tag
def has_similar_recipe(my_account, recipe):
    if my_account:
        matching = my_account.recipes.filter(name=recipe.name)
        if matching:
            return matching.last()
    return False
