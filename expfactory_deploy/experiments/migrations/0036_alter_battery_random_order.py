# Generated by Django 4.1.3 on 2023-08-01 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0035_remove_subject_mturk_id_assignment_group_index_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='battery',
            name='random_order',
            field=models.BooleanField(default=False),
        ),
    ]