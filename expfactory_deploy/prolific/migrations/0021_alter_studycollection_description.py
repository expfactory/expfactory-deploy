# Generated by Django 4.1.3 on 2024-03-20 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prolific", "0020_studycollectionsubject_status_reason_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="studycollection",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Description of the study for the participants to read before starting the study.",
            ),
        ),
    ]
