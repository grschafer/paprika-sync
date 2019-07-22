from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers, fields, relations


class UidManyRelatedField(serializers.ManyRelatedField):
    def to_internal_value(self, data):
        """
        Overriding this so that a SkipField can be taken to mean "ignore this
        category uid because we can't find it in the database" instead of
        "let's skip the entire categories field and return nothing for it"
        """
        if isinstance(data, type('')) or not hasattr(data, '__iter__'):
            self.fail('not_a_list', input_type=type(data).__name__)
        if not self.allow_empty and len(data) == 0:
            self.fail('empty')

        # Original code:
        # return [
        #     self.child_relation.to_internal_value(item)
        #     for item in data
        # ]
        agg = []
        for item in data:
            try:
                agg.append(self.child_relation.to_internal_value(item))
            except fields.SkipField:
                pass
        return agg


class UidRelatedField(serializers.RelatedField):
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid uid "{uid_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected uid value, received {data_type}.'),
    }

    def __init__(self, *args, ignore_missing_relation=False, **kwargs):
        self.ignore_missing_relation = ignore_missing_relation
        super().__init__(*args, **kwargs)

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        Overriding this to use UidManyRelatedField, so if we don't find a
        Category for a given uid, we can ignore that uid instead of
        SkipField-ing and not assigning any Categories at all
        """
        list_kwargs = {'child_relation': cls(*args, **kwargs)}
        for key in kwargs:
            if key in relations.MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]
        return UidManyRelatedField(**list_kwargs)

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(uid=data)
        except ObjectDoesNotExist:
            if self.ignore_missing_relation:
                raise fields.SkipField
            self.fail('does_not_exist', uid_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        return value.uid
