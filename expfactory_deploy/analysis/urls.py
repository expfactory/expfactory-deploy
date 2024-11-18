from django.urls import include, path, re_path
from analysis import views

app_name = "analysis"
urlpatterns = [
    path("qa_by_sc/<int:id>", views.qa_by_sc, name="qa-by-sc"),
    path(
        "trigger_qa_by_sc/<int:id>/",
        views.trigger_qa_by_sc,
        {"rerun": False},
        name="trigger-qa-by-sc",
    ),
    path(
        "trigger_qa_by_sc/<int:id>/rerun",
        views.trigger_qa_by_sc,
        {"rerun": True},
        name="trigger-qa-by-sc-rerun",
    ),
    path(
        "trigger_qa_by_sc_chunked/<int:id>/",
        views.trigger_qa_by_sc_chunked,
        name="trigger-qa-by-sc-rerun_chunked",
    ),
]
