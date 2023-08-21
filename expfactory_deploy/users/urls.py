from django.urls import path

from expfactory_deploy.users.views import (
    view_token,
    user_detail_view,
    user_redirect_view,
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("token/", view_token, {'regenerate': False}, name="token_list"),
    path("token/new", view_token, {'regenerate': True}, name="token_create"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
