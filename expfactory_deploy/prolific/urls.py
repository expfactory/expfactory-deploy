
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
    path("collection/<int:collection_id>/add_participants/", views.ParticipantFormView.as_view(), name="add-participants"),
    path("remote/study/<str:id>", views.remote_study_detail, name="remmote-study-list"),
]
