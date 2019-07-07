from django.contrib import admin

from fsm_admin.mixins import FSMTransitionMixin
from django_fsm_log.admin import StateLogInline

from .models import PaprikaAccount, Recipe, Category, NewsItem


@admin.register(PaprikaAccount)
class PaprikaAccountAdmin(FSMTransitionMixin, admin.ModelAdmin):
    list_display = ('id', 'user', 'username', 'alias')
    readonly_fields = ('import_sync_status',)
    fsm_field = ('import_sync_status',)
    inlines = (StateLogInline,)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'paprika_account', 'name')
    list_filter = ('paprika_account__alias',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'paprika_account', 'name')


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'paprika_account', 'type', 'created_date')
