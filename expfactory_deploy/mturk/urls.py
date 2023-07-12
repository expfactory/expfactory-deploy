from django.urls import path, re_path

from expfactory_deploy.mturk import views

urlpatterns = [
    path("mturk/create", views.HitGroupCreateUpdate.as_view(), name="create-hit"),
    path(
        "mturk/create/<int:battery_id>",
        views.HitGroupCreateUpdate.as_view(),
        name="create-hit",
    ),
    path(
        "mturk/update/<int:pk>", views.HitGroupCreateUpdate.as_view(), name="update-hit"
    ),
    path("mturk/list", views.hits_list, name="hits-list"),
    re_path("mturk/list/(?P<url>.+)", views.hits_list, name="hits-list"),
    path("mturk/list_summaries", views.summaries_list, name="summaries-list"),
    re_path(
        "mturk/list_assignments/(?P<url>.+)",
        views.assignments_list,
        name="assignments-list",
    ),
    re_path(
        "mturk/expire/(?P<hit_id>.+)",
        views.expire_hit,
        name="expire-hit",
    ),
]

app_name = "mturk"
