from django.urls import include, path

from expfactory_deploy.experiments import views

urlpatterns = [
    path("", views.ExperimentRepoList.as_view(), name="home"),
    path(
        "experiments", views.ExperimentRepoList.as_view(), name="experiment-repo-list"
    ),
    path(
        "preview/<int:exp_id>/",
        views.Preview.as_view(),
        name="preview",
    ),
    path(
        "experiment_repo/<int:pk>/",
        views.ExperimentRepoDetail.as_view(),
        name="experiment-repo-detail",
    ),
    path(
        "experiment_repo/add/",
        views.add_new_experiments,
        name="experiment-repo-create",
    ),
    path(
        "repo/add/",
        views.RepoOriginCreate.as_view(),
        name="repo-origin-create",
    ),
    path(
        "experiment_repo/<int:pk>/update/",
        views.ExperimentRepoUpdate.as_view(),
        name="experiment-repo-update",
    ),
    path(
        "experiment_repo/<int:pk>/delete/",
        views.ExperimentRepoDelete.as_view(),
        name="experiment-repo-delete",
    ),
    path("battery/", views.BatteryList.as_view(), name="battery-list"),
    path("battery/<int:pk>/", views.BatteryDetail.as_view(), name="battery-detail"),
    path("battery/create/", views.BatteryComplex.as_view(), name="battery-create"),
    path("battery/<int:pk>/clone", views.BatteryClone.as_view(), name="battery-clone"),
    path(
        "battery/<int:pk>/update/",
        views.BatteryComplex.as_view(),
        name="battery-update",
    ),
    path(
        "battery/<int:battery_id>/deploy/",
        views.BatteryComplex.as_view(),
        name="battery-create",
    ),
    path(
        "serve/<int:subject_id>/<int:battery_id>/",
        views.Serve.as_view(),
        name="serve-battery",
    ),
    path(
        "serve/<int:subject_id>/<int:battery_id>/<int:experiment_id>/",
        views.Serve.as_view(),
        name="serve-experiment",
    ),
    path("subjects/", views.SubjectList.as_view(), name="subject-list"),
    path("subjects/create", views.CreateSubjects.as_view(), name="subjects-create"),
    path("sync/<int:assignment_id>/<int:experiment_id>/", views.Results.as_view(), name="push-results"),
]

""" urls we may want
path('battery/<int:pk>/preview/', views.battery_preview, name='battery-preview'),
path('battery/<int:pk>/serve/', views.battery_serve, name='battery-serve'),
path('results/<int:bid>/<int:expid>/<int:wid>/ views.results, name='results'),
"""
app_name = "experiments"
