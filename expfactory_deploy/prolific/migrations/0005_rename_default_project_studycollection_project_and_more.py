# Generated by Django 4.1.3 on 2023-09-06 14:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("prolific", "0004_prolificapiresult_remove_study_completion_url_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="studycollection",
            old_name="default_project",
            new_name="project",
        ),
        migrations.RemoveField(
            model_name="study",
            name="study_name",
        ),
        migrations.AddField(
            model_name="prolificapiresult",
            name="collection",
            field=models.ForeignKey(
                blank=True,
                default="",
                on_delete=django.db.models.deletion.CASCADE,
                to="prolific.studycollection",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="studycollection",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="studycollection",
            name="estimated_completion_time",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="studycollection",
            name="title",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="studycollection",
            name="total_available_places",
            field=models.IntegerField(default=0),
        ),
    ]
