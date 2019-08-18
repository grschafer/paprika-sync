import logging

import requests.exceptions

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, RedirectView, DetailView, TemplateView

from .forms import PaprikaAccountForm
from .models import PaprikaAccount, NewsItem, Recipe


logger = logging.getLogger(__name__)


# Helpful reference for django class-based views: http://ccbv.co.uk/


class HomeView(LoginRequiredMixin, ListView):
    queryset = NewsItem.objects.all().order_by('-created_date')
    paginate_by = 25
    # Uses template paprika_account/templates/core/newsitem_list.html


class AboutView(TemplateView):
    template_name = 'core/about.html'


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
            # Don't create account if fetching from paprika API fails
            with transaction.atomic():
                return super().post(request, *args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.exception('Error importing account for user %s: %s', request.user, e)
            messages.error(request, 'Error importing account: {}'.format(e))
            return self.get(request, *args, **kwargs)


class RequestAccountSyncView(LoginRequiredMixin, RedirectView):
    http_method_names = ['post']
    pattern_name = 'core:recipes'

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
        try:
            return self.request.user.paprika_accounts.get().recipes.order_by('name')
        except PaprikaAccount.DoesNotExist:
            raise Http404


class RecipeGridView(LoginRequiredMixin, ListView):
    template_name = 'core/recipe_grid.html'
    paginate_by = 25

    def get_queryset(self):
        try:
            return self.request.user.paprika_accounts.get().recipes.order_by('name')
        except PaprikaAccount.DoesNotExist:
            raise Http404


class RecipeDetailView(LoginRequiredMixin, DetailView):
    # Don't require that the user owns the recipe (so you can view others' recipes)
    queryset = Recipe.objects.all()


class RecipeDiffView(LoginRequiredMixin, DetailView):
    template_name = 'core/recipe_diff.html'
    queryset = Recipe.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        other_recipe = Recipe.objects.get(pk=self.kwargs['other_pk'])
        context['other'] = other_recipe
        return context


class RecipeListDiffView(LoginRequiredMixin, ListView):
    template_name = 'core/recipes_diff.html'
    context_object_name = 'diff_list'
    # paginate_by = 25

    def get_queryset(self):
        try:
            other_account = PaprikaAccount.objects.get(alias=self.kwargs['other_alias'])
            return self.request.user.paprika_accounts.get().compare_accounts(other_account)
        except PaprikaAccount.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['my_account'] = self.request.user.paprika_accounts.get()
            context['other_account'] = PaprikaAccount.objects.get(alias=self.kwargs['other_alias'])
        except PaprikaAccount.DoesNotExist:
            raise Http404
        return context


class AccountListView(LoginRequiredMixin, ListView):
    queryset = PaprikaAccount.objects.all()
