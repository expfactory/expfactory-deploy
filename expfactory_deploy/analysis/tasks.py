from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMessage, mail_managers
from django.db.models import Exists, F, OuterRef
from django.urls import reverse

from django_q.tasks import schedule

from analysis.management.commands.run_qa import run_qa
from experiments.models import Result

def run_qa_chunk(sc_id, offset_id, size, delay):
    results = Result.objects.filter(
        subject__studycollectionsubject__study_collection=sc_id,
        id__gt=offset_id
    )[:size]
    results = results.annotate(
        task_name=F("battery_experiment__experiment_instance__experiment_repo_id__name")
    )

    if not results and offset_id != 0:
        message = EmailMessage(
            f"QA Rerun Complete for study collection {sc_id}",
            f"{reverse('analysis:qa-by-sc', kwargs={'id': sc_id})}",
            settings.SERVER_EMAIL,
            [a[1] for a in settings.MANAGERS]
        )
        message.send()
    if not results:
        return

    run_qa(results, rerun=True)

    schedule(
        "analysis.tasks.run_qa_chunk",
            sc_id,
            results.last().id,
            size,
            delay,
            next_run=datetime.now() + delay,
        )
