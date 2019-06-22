import logging

import requests.exceptions

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import PaprikaAccountForm
from .models import PaprikaAccount, NewsItem


logger = logging.getLogger(__name__)


class HomeView(LoginRequiredMixin, ListView):
    queryset = NewsItem.objects.all()
    paginate_by = 25


class AddPaprikaAccountView(LoginRequiredMixin, CreateView):

    form_class = PaprikaAccountForm
    model = PaprikaAccount
    success_url = reverse_lazy('core:home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # TODO: could pass request.user in as 'initial' and make it a hidden field in the form
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        if self.object.import_sync_status == PaprikaAccount.IMPORT_DEFERRED:
            messages.info(self.request, 'Your account contains many recipes! Importing will occur in the background over the next few minutes.')
        return super().get_success_url()

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.exception('Error importing account for user %s: %s', request.user, e)
            messages.error(request, 'Error importing account: {}'.format(e))
            return self.get(request, *args, **kwargs)


home = HomeView.as_view()
add_paprika_account = AddPaprikaAccountView.as_view()
