from django.contrib import admin
from prolific.models import *
from django.apps import apps

for model in apps.get_app_config('prolific').models.values():
    admin.site.register(model)
