import logging

import requests.exceptions

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, RedirectView, DetailView

from .forms import PaprikaAccountForm
from .models import PaprikaAccount, NewsItem, Recipe


logger = logging.getLogger(__name__)


# Helpful reference for django class-based views: http://ccbv.co.uk/


class HomeView(LoginRequiredMixin, ListView):
    queryset = NewsItem.objects.all()
    paginate_by = 25
    # Uses template paprika_account/templates/core/newsitem_list.html


class AddPaprikaAccountView(LoginRequiredMixin, CreateView):
    form_class = PaprikaAccountForm
    model = PaprikaAccount
    success_url = reverse_lazy('core:home')
    # Uses template paprika_account/templates/core/paprikaaccount_form.html

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


class RequestAccountSyncView(LoginRequiredMixin, RedirectView):
    http_method_names = ['post']
    pattern_name = 'core:home'

    def post(self, request, *args, **kwargs):
        for pa in request.user.paprika_accounts.all():
            if pa.import_sync_status == PaprikaAccount.SYNC_SUCCESS:
                pa.request_sync_recipes(by=request.user)
                pa.save()
                messages.success(request, 'Sync requested for account {}, it should begin within 1 minute.'.format(pa))
            else:
                messages.warning(request, 'Sync not requested for account {}, it is in state={}, expected state={}.'.format(pa, pa.import_sync_status, PaprikaAccount.SYNC_SUCCESS))
        return super().post(request, *args, **kwargs)


class RecipeListView(LoginRequiredMixin, ListView):
    # paginate_by = 25

    def get_queryset(self):
        return self.request.user.paprika_accounts.first().recipes.order_by('name')


class RecipeGridView(LoginRequiredMixin, ListView):
    template_name = 'core/recipe_grid.html'
    paginate_by = 25

    def get_queryset(self):
        return self.request.user.paprika_accounts.first().recipes.order_by('name')


class RecipeDetailView(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        return self.request.user.paprika_accounts.first().recipes


class RecipeDiffView(LoginRequiredMixin, DetailView):
    template_name = 'core/recipe_diff.html'

    def get_queryset(self):
        return self.request.user.paprika_accounts.first().recipes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        other_recipe = Recipe.objects.get(pk=self.kwargs['other_pk'])
        context['other'] = other_recipe
        return context
