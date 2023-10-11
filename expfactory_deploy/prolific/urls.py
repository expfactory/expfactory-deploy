
from django.urls import include, path, re_path

from expfactory_deploy.prolific import views

app_name = 'prolific'
urlpatterns = [
    path("serve/<int:battery_id>", views.ProlificServe.as_view(), name="serve-battery"),
    path("complete/<int:assignment_id>", views.ProlificComplete.as_view(), name="complete"),
    path("simplecc/update/<int:battery_id>", views.SimpleCCUpdate.as_view(), name="update-simple-cc"),
    path("collection/new", views.StudyCollectionView.as_view(), name="collection-create"),
    path("collection/<int:collection_id>", views.StudyCollectionView.as_view(), name="study-collection-update"),
    path("collection/", views.StudyCollectionList.as_view(), name="study-collection-list"),
    path("collection/<int:collection_id>/create_drafts/", views.create_drafts_view, name="create-drafts"),
    path("collection/<int:collection_id>/publish/", views.publish_drafts, name="publish-drafts"),
    path("collection/<int:collection_id>/add_participants/", views.ParticipantFormView.as_view(), name="add-participants"),
    path("collection/<int:collection_id>/progress", views.collection_progress, name="collection-progress"),
    path("collection/<int:collection_id>/toggle", views.toggle_collection, name="collection-toggle"),
    path("collection/<int:collection_id>/clear_remote_ids", views.clear_remote_ids, name="collection-clear-remote-ids"),
    path("remote/studies/", views.remote_studies_list, name="remote-studies-list"),
    path("remote/studies/<str:id>", views.remote_studies_list, name="remote-studies-list"),
    path("remote/study/<str:id>", views.remote_study_detail, name="remote-study-detail"),
]
