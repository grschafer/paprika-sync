from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("add-paprika-account", view=views.AddPaprikaAccountView.as_view(), name="add_paprika_account"),
    path("request-account-sync", view=views.RequestAccountSyncView.as_view(), name="request_account_sync"),
    path("recipes", view=views.RecipeListView.as_view(), name="recipes"),
    path("grid", view=views.RecipeGridView.as_view(), name="recipe-grid"),
    path("recipe/<int:pk>", view=views.RecipeDetailView.as_view(), name="recipe"),
    path("recipe/<int:pk>/diff/<int:other_pk>", view=views.RecipeDiffView.as_view(), name="recipe-diff"),
]
