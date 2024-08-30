from django.urls import include, path, re_path

from expfactory_deploy.prolific import api_views

app_name = "prolific_api"

urlpatterns = [
    path("api/warnings", api_views.prolific_warnings, name="prolific-warnings"),
    path("api/kicks", api_views.prolific_kicks, name="prolific-kicks"),
    path("api/suspensions", api_views.prolific_suspensions, name="prolific-suspensions"),
]
