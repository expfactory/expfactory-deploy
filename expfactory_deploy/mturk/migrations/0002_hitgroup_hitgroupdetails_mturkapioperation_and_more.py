# Generated by Django 4.1.3 on 2023-04-27 15:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("experiments", "0033_alter_battery_group"),
        ("users", "0002_group_membership_group_members"),
        ("mturk", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="HitGroup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("sandbox", models.BooleanField(default=True)),
                ("note", models.TextField(blank=True)),
                ("published", models.DateTimeField(blank=True, null=True)),
                ("number_of_assignments", models.IntegerField()),
                (
                    "battery",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="experiments.battery",
                    ),
                ),
                (
                    "credentials",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mturk.mturkcredentials",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HitGroupDetails",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.TextField()),
                ("description", models.TextField()),
                ("keywords", models.TextField(blank=True)),
                ("reward", models.DecimalField(decimal_places=2, max_digits=10)),
                ("auto_approval_delay", models.IntegerField(blank=True)),
                ("lifetime_in_hours", models.IntegerField(default=168)),
                ("assignment_duration_in_hours", models.IntegerField(default=168)),
                (
                    "qualification_requirements",
                    models.JSONField(
                        default=[
                            {
                                "Comparator": "EqualTo",
                                "LocaleValues": [{"Country": "US"}],
                                "QualificationTypeId": "00000000000000000071",
                            }
                        ]
                    ),
                ),
                (
                    "request_annotation",
                    models.UUIDField(default=uuid.uuid4, editable=False),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MturkApiOperation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("response", models.TextField()),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "group",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.group",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HitGroupHits",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("hit_id", models.TextField()),
                ("unique_request_token", models.TextField(blank=True)),
                (
                    "hit_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="mturk.hitgroup"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="hitgroup",
            name="details",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="mturk.hitgroupdetails"
            ),
        ),
        migrations.AddField(
            model_name="hitgroup",
            name="parent",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="mturk.hitgroup"
            ),
        ),
    ]