from django.urls import include, path, re_path

from expfactory_deploy.experiments import views
from expfactory_deploy.experiments import api_views

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
        "preview/<int:exp_id>/<str:commit>",
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
        "repo/pull/",
        views.RepoOriginPull.as_view(),
        name="repo-origin-pull",
    ),
    path(
        "repo/list/",
        views.RepoOriginList.as_view(),
        name="repo-origin-list",
    ),
    path(
        "repo/<int:pk>/",
        views.RepoOriginDetail.as_view(),
        name="repo-origin-detail",
    ),
    path("repo/<int:pk>/deactivate", views.deactivate_repo, name="repo-deactivate"),
    path(
        "repo/<int:pk>/deactivate/confirm",
        views.deactivate_repo_confirmation,
        name="repo-deactivate-confirm",
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
    path(
        "experiment_repo/tags/add/",
        views.ExperimentRepoBulkTag.as_view(),
        name="experiment-repo-bulk-tag-add",
        kwargs={"action": "add"},
    ),
    path(
        "experiment_repo/tags/remove/",
        views.ExperimentRepoBulkTag.as_view(),
        name="experiment-repo-bulk-tag-remove",
        kwargs={"action": "remove"},
    ),
    path(
        "experiment_instance/<int:pk>/update/",
        views.ExperimentInstanceUpdate.as_view(),
        name="experiment-instance-update",
    ),
    path(
        "experiment_instance/add/",
        views.ExperimentInstanceCreate.as_view(),
        name="experiment-instance-create",
    ),
    path(
        "experiment_instance/<int:pk>",
        views.ExperimentInstanceDetail.as_view(),
        name="experiment-instance-detail",
    ),
    path(
        "repo/form/<int:repo_id>/",
        views.instance_order_form,
        name="instance-order-form",
    ),
    path("battery/", views.BatteryList.as_view(), name="battery-list"),
    re_path("battery/(?P<status>inactive)", views.BatteryList.as_view(), name="battery-list"),
    path("battery/<int:pk>/", views.BatteryDetail.as_view(), name="battery-detail"),
    path("battery/create/", views.BatteryComplex.as_view(), name="battery-create"),
    path("battery/<int:pk>/clone", views.BatteryClone.as_view(), name="battery-clone"),
    path("battery/<int:pk>/publish", views.publish_battery, name="battery-publish"),
    path(
        "battery/<int:pk>/publish/confirm",
        views.publish_battery_confirmation,
        name="battery-publish-confirm",
    ),
    path(
        "battery/<int:pk>/deactivate",
        views.deactivate_battery,
        name="battery-deactivate",
    ),
    path(
        "battery/<int:pk>/deactivate/confirm",
        views.deactivate_battery_confirmation,
        name="battery-deactivate-confirm",
    ),
    path(
        "battery/<int:pk>/propagate/instructions",
        views.propagate_instructions,
        name="propagate-instructions",
    ),

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
    path(
        "battery/<int:battery_id>/export",
        views.battery_results,
        name="export-battery",
    ),
    path(
        "subject/<int:subject_id>/export",
        views.subject_results,
        name="export-subject",
    ),
    path("subjects/", views.SubjectList.as_view(), name="subject-list"),
    path(
        "subjects/toggle",
        views.ToggleSubjectActivation.as_view(),
        name="subject-toggle",
    ),
    path("subjects/assign", views.AssignSubject.as_view(), name="subject-assign"),
    path("subjects/create", views.CreateSubjects.as_view(), name="subjects-create"),
    path("subject/<int:pk>/", views.SubjectDetail.as_view(), name="subject-detail"),
    path(
        "sync/<int:assignment_id>/<int:experiment_id>/",
        views.Results.as_view(),
        name="push-results",
    ),
    path("results/<int:result_id>/", views.single_result, name="result-detail"),
    path("assignments/generate/<int:battery_id>/<int:num_subjects>", views.batch_assignment_create, name="assignment-generate"),
    path("serve/complete", views.Complete.as_view(), name="complete"),
    path("serve/<int:assignment_id>/consent", views.ServeConsent.as_view(), name="consent"),
    path("serve/preview/<int:battery_id>/consent", views.PreviewConsent.as_view(), name="preview-consent"),
    path("api/results/battery/<int:battery_id>/", api_views.get_results_view, name="api-results-by-battery"),
    path("api/results/subject/<int:subject_id>/", api_views.get_results_view, name="api-results-by-subject"),
]

app_name = "experiments"
