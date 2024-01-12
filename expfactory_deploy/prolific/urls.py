from django.urls import include, path, re_path

from expfactory_deploy.prolific import views

app_name = "prolific"
urlpatterns = [
    path("serve/<int:battery_id>", views.ProlificServe.as_view(), name="serve-battery"),
    path(
        "complete/<int:assignment_id>",
        views.ProlificComplete.as_view(),
        name="complete",
    ),
    path(
        "simplecc/update/<int:battery_id>",
        views.SimpleCCUpdate.as_view(),
        name="update-simple-cc",
    ),
    path(
        "collection/new", views.StudyCollectionView.as_view(), name="collection-create"
    ),
    path(
        "collection/<int:collection_id>",
        views.StudyCollectionView.as_view(),
        name="study-collection-update",
    ),
    path(
        "collection/", views.StudyCollectionList.as_view(), name="study-collection-list"
    ),
    path(
        "collection/<int:collection_id>/create_drafts/",
        views.create_drafts_view,
        name="create-drafts",
    ),
    path(
        "collection/<int:collection_id>/publish/",
        views.publish_drafts,
        name="publish-drafts",
    ),
    path(
        "collection/<int:collection_id>/add_participants/",
        views.ParticipantFormView.as_view(),
        name="add-participants",
    ),
    path(
        "collection/<int:collection_id>/progress",
        views.collection_progress,
        name="collection-progress",
    ),
    path(
        "collection/<int:collection_id>/progress_by_data",
        views.collection_progress_by_experiment_submissions,
        name="collection-progress-by-data",
    ),
    path(
        "collection/<int:collection_id>/progress_by_prolific_submissions",
        views.collection_progress_by_prolific_submissions,
        name="collection-progress-by-prolific",
    ),
    path(
        "collection/<int:collection_id>/progress/recent/result/<int:days>",
        views.collection_recently_completed,
        {"by": "result"},
        name="collection-recent-result",
    ),
    path(
        "collection/<int:collection_id>/progress/recent/assignment/<int:days>",
        views.collection_recently_completed,
        {"by": "assignment"},
        name="collection-recent-assignment",
    ),
    path(
        "collection/<int:collection_id>/toggle",
        views.toggle_collection,
        name="collection-toggle",
    ),
    path(
        "collection/<int:collection_id>/clear_remote_ids",
        views.clear_remote_ids,
        name="collection-clear-remote-ids",
    ),
    path(
        "collection/<int:collection_id>/subjects",
        views.study_collection_subject_list,
        name="collection-subject-list",
    ),
    path(
        "collection/subject/<int:scs_id>",
        views.study_collection_subject_detail,
        name="collection-subject-detail",
    ),
    path(
        "collection/<int:collection_id>/subject/<prolific_id>",
        views.study_collection_subject_detail,
        name="collection-subject-detail",
    ),
    path("remote/studies/", views.remote_studies_list, name="remote-studies-list"),
    path(
        "remote/studies/<str:collection_id>",
        views.remote_studies_list,
        name="remote-studies-list",
    ),
    path(
        "remote/study/<str:id>", views.remote_study_detail, name="remote-study-detail"
    ),
    path(
        "blocked_participant/list",
        views.BlockedParticipantList.as_view(),
        name="blocked-participant-list",
    ),
    path(
        "blocked_participant/create",
        views.BlockedParticipantCreate.as_view(),
        name="blocked-participant-create",
    ),
    path(
        "blocked_participant/update/<int:pk>",
        views.BlockedParticipantUpdate.as_view(),
        name="blocked-participant-update",
    ),
    path("recent/participants", views.recent_participants, name="recent-participants"),
]
