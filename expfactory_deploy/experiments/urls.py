from django.urls import include, path

from expfactory_deploy.experiments import views

urlpatterns = [
    path("", views.ExperimentRepoList.as_view(), name="experiment-repo-list"),
    path(
        "experiment_repo/<int:pk>/",
        views.ExperimentRepoDetail.as_view(),
        name="experiment-repo-detail",
    ),
    path(
        "experiment_repo/add/",
        views.find_new_experiments,
        name="experiment-repo-create",
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
]

""" urls we may want
path('battery/<int:pk>/preview/', views.battery_preview, name='battery-preview'),
path('battery/<int:pk>/serve/', views.battery_serve, name='battery-serve'),
path('results/<int:bid>/<int:expid>/<int:wid>/ views.results, name='results'),
"""
app_name = "experiments"
