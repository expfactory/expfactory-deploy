# Generated by Django 4.1.3 on 2024-01-10 20:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("prolific", "0013_studysubject_prolific_session_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="studycollection",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="children",
                to="prolific.studycollection",
            ),
        ),
    ]
