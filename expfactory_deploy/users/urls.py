from django.urls import path

from expfactory_deploy.users.views import (
    token_create,
    token_list,
    user_detail_view,
    user_redirect_view,
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    re_path(r"^token/$", view_token, {'regenerate': False}, name="token_list"),
    re_path(r"^token/new$", view_token, {'regenerate': True}, name="token_create"),
]
