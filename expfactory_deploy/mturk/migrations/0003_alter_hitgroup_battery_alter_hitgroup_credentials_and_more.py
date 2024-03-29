# Generated by Django 4.1.3 on 2023-05-02 19:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0033_alter_battery_group"),
        ("mturk", "0002_hitgroup_hitgroupdetails_mturkapioperation_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hitgroup",
            name="battery",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="experiments.battery",
            ),
        ),
        migrations.AlterField(
            model_name="hitgroup",
            name="credentials",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="mturk.mturkcredentials",
            ),
        ),
        migrations.AlterField(
            model_name="hitgroup",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="mturk.hitgroup",
            ),
        ),
    ]
