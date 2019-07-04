from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers, fields


class UidRelatedField(serializers.RelatedField):
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid uid "{uid_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected uid value, received {data_type}.'),
    }

    def __init__(self, *args, ignore_missing_relation=False, **kwargs):
        self.ignore_missing_relation = ignore_missing_relation
        super().__init__(*args, **kwargs)

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
