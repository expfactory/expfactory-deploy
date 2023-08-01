
from django.urls import include, path, re_path

from expfactory_deploy.prolific import views

app_name = 'prolific'
urlpatterns = [
    path("serve/<int:battery_id>", views.ProlificServe.as_view(), name="serve-battery"),
    path("complete/<int:assignment_id>", views.ProlificComplete.as_view(), name="consent"),
    path("simplecc/update/<int:battery_id>", views.SimpleCCUpdate.as_view(), name="update-simple-cc"),
]
