
from django.urls import include, path, re_path

from expfactory_deploy.prolific import views

urlpatterns = [
    path("prolific/serve/<int:battery_id>", views.ProlificServe.as_view(), name="serve-battery"),
    path("complete/<int:assignment_id>", views.ProlificComplete.as_view(), name="consent"),
    path("simplecc/create/<int:battery_id>", views.SimpleCCCreate.as_view(), name="create-simple-cc"),
    path("simplecc/update/<int:pk>", views.SimpleCCUpdate.as_view(), name="update-simple-cc"),
]
