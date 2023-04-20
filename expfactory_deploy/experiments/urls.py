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
        "battery/preview/<int:battery_id>/",
        views.PreviewBattery.as_view(),
        name="preview-battery",
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
        "repo/list/",
        views.RepoOriginList.as_view(),
        name="repo-origin-list",
    ),
    path("repo/<int:pk>/deactivate", views.deactivate_repo, name="repo-deactivate"),
    path("repo/<int:pk>/deactivate/confirm", views.deactivate_repo_confirmation, name="repo-deactivate-confirm"),
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

    path(
        "experiment_repo/tags/add/",
        views.ExperimentRepoBulkTag.as_view(),
        name="experiment-repo-bulk-tag-add",
        kwargs={'action': 'add'}
    ),
    path(
        "experiment_repo/tags/remove/",
        views.ExperimentRepoBulkTag.as_view(),
        name="experiment-repo-bulk-tag-remove",
        kwargs={'action': 'remove'}
    ),
    path(
        "experiment_instance/<int:pk>/update/",
        views.ExperimentInstanceUpdate.as_view(),
        name="experiment-instance-update"
    ),
    path(
        "experiment_instance/add/",
        views.ExperimentInstanceCreate.as_view(),
        name="experiment-instance-create"
    ),
    path(
        "experiment_instance/<int:pk>",
        views.ExperimentInstanceDetail.as_view(),
        name="experiment-instance-detail"
    ),
    path(
        "repo/form/<int:repo_id>/",
        views.instance_order_form,
        name="instance-order-form"
    ),
    path("battery/", views.BatteryList.as_view(), name="battery-list"),
    path("battery/<int:pk>/", views.BatteryDetail.as_view(), name="battery-detail"),
    path("battery/create/", views.BatteryComplex.as_view(), name="battery-create"),
    path("battery/<int:pk>/clone", views.BatteryClone.as_view(), name="battery-clone"),
    path("battery/<int:pk>/publish", views.publish_battery, name="battery-publish"),
    path("battery/<int:pk>/publish/confirm", views.publish_battery_confirmation, name="battery-publish-confirm"),
    path("battery/<int:pk>/deactivate", views.deactivate_battery, name="battery-deactivate"),
    path("battery/<int:pk>/deactivate/confirm", views.deactivate_battery_confirmation, name="battery-deactivate-confirm"),
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
        "serve/<int:battery_id>/",
        views.Serve.as_view(),
        name="serve-battery",
    ),
    path(
        "serve/<int:subject_id>/<int:battery_id>/<int:experiment_id>/",
        views.Serve.as_view(),
        name="serve-experiment",
    ),
    path("subjects/", views.SubjectList.as_view(), name="subject-list"),
    path("subjects/toggle", views.ToggleSubjectActivation.as_view(), name="subject-toggle"),
    path("subjects/assign", views.AssignSubject.as_view(), name="subject-assign"),
    path("subjects/create", views.CreateSubjects.as_view(), name="subjects-create"),
    path("subjects/<int:pk>/", views.SubjectDetail.as_view(), name="subject-detail"),
    path("sync/<int:assignment_id>/<int:experiment_id>/", views.Results.as_view(), name="push-results"),

]

app_name = "experiments"
