# Generated by Django 4.1.3 on 2024-03-12 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prolific", "0017_remove_studysubject_prolific_session_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="studycollection",
            name="failure_to_start_message",
            field=models.TextField(blank=True),
        ),
    ]
