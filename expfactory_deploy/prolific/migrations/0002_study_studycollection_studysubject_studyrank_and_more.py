# Generated by Django 4.1.3 on 2023-08-21 14:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0038_remove_assignment_prolific_id"),
        ("prolific", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Study",
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
                ("completion_url", models.URLField(blank=True, max_length=65536)),
                ("study_name", models.TextField(blank=True)),
                (
                    "battery",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="experiments.battery",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StudyCollection",
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
                ("name", models.TextField(blank=True)),
                ("default_project", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="StudySubject",
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
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="experiments.assignment",
                    ),
                ),
                (
                    "study",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="prolific.study"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StudyRank",
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
                (
                    "rank",
                    models.IntegerField(default=0, verbose_name="Experiment order"),
                ),
                (
                    "study",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="prolific.study"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="study",
            name="study_collection",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="prolific.studycollection",
            ),
        ),
    ]
