from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import PaprikaAccountForm
from .models import PaprikaAccount


class AddPaprikaAccountView(LoginRequiredMixin, CreateView):

    form_class = PaprikaAccountForm
    model = PaprikaAccount
    success_url = reverse_lazy('home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # TODO: could pass request.user in as 'initial' and make it a hidden field in the form
        kwargs['user'] = self.request.user
        return kwargs


add_paprika_account = AddPaprikaAccountView.as_view()
