from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("add-paprika-account", view=views.AddPaprikaAccountView.as_view(), name="add_paprika_account"),
    path("request-account-sync", view=views.RequestAccountSyncView.as_view(), name="request_account_sync"),
]
