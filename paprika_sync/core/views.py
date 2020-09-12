import logging

import requests.exceptions

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, ListView, RedirectView, DetailView, TemplateView

from rest_framework import exceptions, permissions, status, renderers, views
from rest_framework.response import Response

from .forms import PaprikaAccountForm
from .models import PaprikaAccount, NewsItem, Recipe


logger = logging.getLogger(__name__)


# Helpful reference for django class-based views: http://ccbv.co.uk/


class HomeView(LoginRequiredMixin, ListView):
    queryset = NewsItem.objects.all().order_by('-created_date', 'id').select_related('recipe', 'previous_recipe', 'paprika_account')
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


# This might be better as an @action on a broader Recipe DRF ViewSet
@login_required
@require_http_methods(['POST'])
def recipe_clone_view(request, pk):
    try:
        pa = request.user.paprika_accounts.get()
    except PaprikaAccount.DoesNotExist:
        logger.exception('User %s tried to clone recipe %s to non-existent account', request.user, pk)
        messages.error(request, 'Your PaprikaAccount was not found! This should not be possible.')
    else:
        try:
            recipe = Recipe.objects.get(id=pk)
        except (KeyError, Recipe.DoesNotExist):
            raise exceptions.NotFound
        pa.clone_recipe(recipe)
        messages.success(request, '''Recipe cloned! Sync in your Paprika app to see the new recipe.<script>document.addEventListener("DOMContentLoaded", function() {{ alert("NOTE: The recipe's categories ({}) were not copied, please add categories to the recipe in your app.") }});</script>'''.format(', '.join(cat.name for cat in recipe.categories.all())))
    return redirect(request.META['HTTP_REFERER'])


# Ajax-ready version of above in case that's useful in the future
'''
def RecipeCloneView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        pa = request.user.paprika_accounts.get()
        recipe = Recipe.objects.get(id=pk)
        pa.clone_recipe(recipe)
        return Response({'message': 'Recipe cloned! Sync in your Paprika app to see the new recipe.', 'alert_message': "NOTE: The recipe's categories ({}) were not copied, please add categories to the recipe in your app.".format(', '.join(cat.name for cat in recipe.categories.all()))})

    def handle_exception(self, exc):
        context = self.get_exception_handler_context()
        if isinstance(exc, PaprikaAccount.DoesNotExist):
            logger.exception('User %s tried to clone recipe %s to non-existent account', context['request'].user, context['kwargs']['pk'])
            return Response({'error': "You don't have a Paprika Account"}, status=status.HTTP_404_NOT_FOUND)
        elif isinstance(Recipe.DoesNotExist):
            logger.exception('User %s tried to clone non-existent recipe %s to account', context['request'].user, context['kwargs']['pk'])
            return Response({'error': "Recipe not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return super().handle_exception(exc)
'''


class RecipeDiffView(LoginRequiredMixin, DetailView):
    template_name = 'core/recipe_diff.html'
    queryset = Recipe.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        other_recipe = Recipe.objects.get(pk=self.kwargs['other_pk'])
        context['other'] = other_recipe
        return context


class AccountRecipeListView(LoginRequiredMixin, ListView):
    # TODO: change this to use recipe_list.html template (same as "Your Recipes" page)
    template_name = 'core/recipes_diff.html'
    context_object_name = 'recipe_list'
    # paginate_by = 25

    def get_queryset(self):
        return PaprikaAccount.objects.get(alias=self.kwargs['other_alias']).recipes.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['other_account'] = PaprikaAccount.objects.get(alias=self.kwargs['other_alias'])
        except PaprikaAccount.DoesNotExist:
            raise Http404
        return context


class FindRecipesView(LoginRequiredMixin, TemplateView):
    template_name = 'core/find_recipes.html'

    def get_context_data(self, **kwargs):
        kwargs['paprika_accounts'] = PaprikaAccount.objects.all()
        return super().get_context_data(**kwargs)


class SearchRecipesView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [renderers.TemplateHTMLRenderer]
    template_name = 'core/search_results.html'

    def get(self, request, format=None):
        # TODO: Possible optimization is to register requests in redis and
        # cancel during querying if a subsequent search request from the same
        # user appears. We'd need to eagerly evaluate querysets, otherwise all
        # the work happens in response-rendering, where we can't really cancel
        # the request.
        query = request.GET['q']
        # TODO: Possible optimization is to make a managed=False model mapping
        # onto recipe table, but containing only
        # name/paprika_account__alias/created/rating because those are the only
        # fields displayed in the search results table
        # https://docs.djangoproject.com/en/3.1/ref/models/querysets/#defer
        recipes = Recipe.objects.filter(date_ended__isnull=True, in_trash=False).order_by('name', 'paprika_account__alias')
        recipes_name = recipes.filter(name__icontains=query)
        # When searching ingredients, match only at the beginning of a word
        # https://www.postgresql.org/docs/current/functions-matching.html#POSIX-CONSTRAINT-ESCAPES-TABLE
        recipes_ingredients = recipes.filter(ingredients__iregex=r'\m{}'.format(query))
        recipes_source = recipes.filter(source__icontains=query)
        return Response({'recipes_name': recipes_name, 'recipes_ingredients': recipes_ingredients, 'recipes_source': recipes_source})
