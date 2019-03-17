from django import forms
from django.utils.translation import ugettext_lazy as _

from .actions import import_account
from .models import PaprikaAccount


class PaprikaAccountForm(forms.ModelForm):
    class Meta:
        model = PaprikaAccount
        fields = ('username', 'password', 'alias')
        widgets = {
            'password': forms.PasswordInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self, **kwargs):
        return import_account(self.user, self.cleaned_data['username'], self.cleaned_data['password'], self.cleaned_data['alias'])
