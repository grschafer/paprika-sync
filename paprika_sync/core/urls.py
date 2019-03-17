from django.urls import path

from .views import (
    add_paprika_account,
    home,
)

app_name = "core"
urlpatterns = [
    path("", home, name="home"),
    path("add-paprika-account", view=add_paprika_account, name="add_paprika_account"),
]
