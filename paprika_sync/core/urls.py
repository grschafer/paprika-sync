from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("accounts/add", view=views.AddPaprikaAccountView.as_view(), name="add-paprika-account"),
    path("account/sync", view=views.RequestAccountSyncView.as_view(), name="request-account-sync"),
    path("recipes", view=views.RecipeListView.as_view(), name="recipes"),
    path("grid", view=views.RecipeGridView.as_view(), name="recipe-grid"),
    path("recipe/<int:pk>", view=views.RecipeDetailView.as_view(), name="recipe"),
    path("recipe/<int:pk>/diff/<int:other_pk>", view=views.RecipeDiffView.as_view(), name="recipe-diff"),
    path("recipes/diff/<str:other_alias>", view=views.RecipeListDiffView.as_view(), name="recipes-diff"),
    path("accounts", view=views.AccountListView.as_view(), name="accounts"),
]
