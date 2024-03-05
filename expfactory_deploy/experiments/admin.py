from django.contrib import admin
from experiments.models import *
from django.apps import apps

for model in apps.get_app_config('experiments').models.values():
    admin.site.register(model)
