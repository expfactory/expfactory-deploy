from django.urls import include, path, re_path
from analysis import views

app_name = "analysis"
urlpatterns = [
    path("qa_by_sc/<int:id>", view.qa_by_sc, name="qa-by-sc"),
    path(
        "trigger_qa_by_sc/<int:id>/",
        view.trigger_qa_by_sc,
        {"rerun": Flase},
        name="trigger-qa-by-sc",
    ),
    path(
        "trigger_qa_by_sc/<int:id>/rerun",
        view.trigger_qa_by_sc,
        {"rerun": True},
        name="trigger-qa-by-sc-rerun",
    ),
]
