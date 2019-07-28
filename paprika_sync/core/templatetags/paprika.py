import os.path

from django import template
from django.db.models.manager import BaseManager

register = template.Library()


@register.simple_tag
def diff(recipe, other, field, sub_field=None, by_url_uid=False):
    mine = getattr(recipe, field)
    yours = getattr(other, field)
    if isinstance(mine, BaseManager) and sub_field:
        mine = sorted(mine.all().values_list(sub_field, flat=True))
        yours = sorted(yours.all().values_list(sub_field, flat=True))
    elif by_url_uid:
        mine = os.path.basename(mine)
        yours = os.path.basename(yours)

    if mine != yours:
        return 'different'
    return ''
