from django.urls import path

from .views import (
    add_paprika_account,
)

app_name = "core"
urlpatterns = [
    path("add-paprika-account", view=add_paprika_account, name="add_paprika_account"),
]
