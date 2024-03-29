# Generated by Django 4.1.3 on 2023-07-11 22:10

from django.db import migrations, models
import django.db.models.deletion
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0033_alter_battery_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True)),
                ('auto_generated', models.BooleanField(default=True)),
                ('battery', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='experiments.battery')),
            ],
        ),
        migrations.AlterField(
            model_name='assignment',
            name='status',
            field=model_utils.fields.StatusField(choices=[('not-started', 'not-started'), ('started', 'started'), ('completed', 'completed'), ('failed', 'failed'), ('redo', 'redo')], default='not-started', max_length=100, no_check_for_status=True),
        ),
        migrations.AlterField(
            model_name='batteryexperiments',
            name='use_latest',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='status',
            field=model_utils.fields.StatusField(choices=[('not-started', 'not-started'), ('started', 'started'), ('completed', 'completed'), ('failed', 'failed'), ('redo', 'redo')], default='not-started', max_length=100, no_check_for_status=True),
        ),
        migrations.CreateModel(
            name='ExperimentOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=0, verbose_name='Experiment order')),
                ('battery_experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='experiments.batteryexperiments')),
                ('experiment_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='experiments.experimentorder')),
            ],
        ),
        migrations.AddField(
            model_name='assignment',
            name='ordering',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='experiments.experimentorder'),
        ),
    ]
