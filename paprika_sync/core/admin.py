from django.contrib import admin

from .models import PaprikaAccount, Recipe


@admin.register(PaprikaAccount)
class PaprikaAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'username', 'alias')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'paprika_account', 'name')
