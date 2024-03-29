# Generated by Django 4.1.3 on 2023-11-10 16:51

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("experiments", "0038_remove_assignment_prolific_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResultQA",
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
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("qa_result", models.JSONField(blank=True)),
                ("passed", models.BooleanField(default=None, null=True)),
                ("error", models.TextField(null=True)),
                (
                    "exp_result",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="experiments.result",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
