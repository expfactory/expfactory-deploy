# Generated by Django 4.1.3 on 2024-03-06 16:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0041_assignment_alt_id"),
        ("prolific", "0016_alter_studycollectionsubject_warned_at"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="studysubject",
            name="prolific_session_id",
        ),
        migrations.AddField(
            model_name="studysubject",
            name="assigned_to_study",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="studysubject",
            name="subject",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="experiments.subject",
            ),
        ),
        migrations.AlterField(
            model_name="studycollection",
            name="collection_grace_interval",
            field=models.DurationField(
                blank=True,
                help_text="hh:mm:ss - Time after warning message is sent to kick participant from remaining studies.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="studycollection",
            name="collection_time_to_warning",
            field=models.DurationField(
                blank=True,
                help_text="hh:mm:ss - Overall time participant has to complete all studies before recieving a warning message.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="studycollection",
            name="study_grace_interval",
            field=models.DurationField(
                blank=True,
                help_text="hh:mm:ss - Time after warning message has been sent to kick participant from the study.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="studycollection",
            name="study_time_to_warning",
            field=models.DurationField(
                blank=True,
                help_text="hh:mm:ss - After completing a study participants will be reminded to start on the next study after this amount of time.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="studycollection",
            name="time_to_start_first_study",
            field=models.DurationField(
                blank=True,
                help_text="hh:mm:ss - Upon adding participant to a study collection, they have this long to start the first study before being removed from study",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="studysubject",
            name="assignment",
            field=models.ForeignKey(
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="experiments.assignment",
            ),
        ),
        migrations.AlterField(
            model_name="studysubject",
            name="study",
            field=models.ForeignKey(
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="prolific.study",
            ),
        ),
        migrations.AddConstraint(
            model_name="studysubject",
            constraint=models.UniqueConstraint(
                fields=("study", "subject"), name="UniqueStudySubject"
            ),
        ),
    ]
