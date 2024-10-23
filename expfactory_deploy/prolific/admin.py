from django.contrib import admin
from prolific.models import *
from django.apps import apps

for model in apps.get_app_config("prolific").models.values():
    admin.site.register(model)

from django_q import models as q_models
from django_q import admin as q_admin

admin.site.unregister([q_models.Schedule])
@admin.register(q_models.Schedule)
class ModedScheduleAdmin(q_admin.ScheduleAdmin):
    list_display = (
        "id",
        "name",
        "func",
        "args",
        "schedule_type",
        "repeats",
        "cluster",
        "next_run",
        "get_last_run",
        "get_success",
    )

admin.site.unregister([q_models.Success])
@admin.register(q_models.Success)
class ModedSuccessAdmin(q_admin.TaskAdmin):
    list_display = (
        "name",
        "group",
        "func",
        "args",
        "cluster",
        "started",
        "stopped",
        "time_taken",
    )
