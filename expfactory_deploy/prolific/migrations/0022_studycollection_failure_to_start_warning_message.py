# Generated by Django 4.1.3 on 2024-03-20 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prolific", "0021_alter_studycollection_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="studycollection",
            name="failure_to_start_warning_message",
            field=models.TextField(blank=True),
        ),
    ]
