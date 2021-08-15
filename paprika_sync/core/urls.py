from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about", view=views.AboutView.as_view(), name="about"),
    path("accounts/add", view=views.AddPaprikaAccountView.as_view(), name="add-paprika-account"),
    path("account/sync", view=views.RequestAccountSyncView.as_view(), name="request-account-sync"),
    path("recipes", view=views.RecipeListView.as_view(), name="recipes"),
    path("grid", view=views.RecipeGridView.as_view(), name="recipe-grid"),
    path("recipe/<int:pk>", view=views.RecipeDetailView.as_view(), name="recipe"),
    path("recipe/<int:pk>/clone", view=views.recipe_clone_view, name="recipe-clone"),
    path("recipe/<int:pk>/diff/<int:other_pk>", view=views.RecipeDiffView.as_view(), name="recipe-diff"),
    path("find", view=views.FindRecipesView.as_view(), name="find-recipes"),
    path("find_old", view=views.FindRecipesOldView.as_view(), name="find-recipes-old"),
    path("find_old/search", view=views.SearchRecipesOldView.as_view(), name="search-recipes"),
    path("find/search", view=views.SearchRecipesView.as_view(), name="search-recipes"),
    path("account/<str:other_alias>/recipes", view=views.AccountRecipeListView.as_view(), name="account-recipes"),
]
