# Generated by Django 3.1.7 on 2021-10-29 18:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0009_remove_battery_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='battery',
            old_name='name2',
            new_name='name',
        ),
    ]
