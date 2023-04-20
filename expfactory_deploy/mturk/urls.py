from django.urls import include, path

from expfactory_deploy.mturk import views

'''
    path("", views.ExperimentRepoList.as_view(), name="home"),
    path("battery/<int:pk>/publish/confirm", views.publish_battery_confirmation, name="battery-publish-confirm"),
    path(
        "experiments", views.ExperimentRepoList.as_view(), name="experiment-repo-list"
    ),
    path(
        "preview/<int:exp_id>/",
        views.Preview.as_view(),
        name="preview",
    ),
'''
urlpatterns = [
    path("mturk/(?P<level>sandbox|production)/create_hit$", views.CreateHit.as_view(), name="create-hit"),
    path("mturk/(?P<level>sandbox|production)/list$", views.list_hits, name="list-hits"),
]

app_name = "mturk"
