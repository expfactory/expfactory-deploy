# Generated by Django 4.1.3 on 2023-11-15 20:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0039_subject_last_exp_subject_last_url_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subject",
            name="last_url_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
