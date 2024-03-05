from experiments import models as em
from prolific import models as pm
from prolific import outgoing_api as api

from django_q.tasks import schedule

"""
on add participant to studycollection:
    - create collection wide timer
        when hit if not all studies complete send message and set grace timer
    - create initial timer
        when hit message? or kick?

on battery completion:
    - create inter study min timer
        When hit add to next participant group
    - create inter study max timer
        when hit check to see if started:
            if not send message and set grace timer
"""
def on_add_to_collection(scs):
    schedule(
        "prolific.tasks.collection_end_time_to_first",
        f"{scs.id}",
        next_run=datetime.now() + scs.time_to_start_first_study,
    )
    schedule(
        "prolific.tasks.collection_warning",
        f"{scs.id}",
        next_run=datetime.now() + scs.time_to_warning,
    )


def on_complete_battery(scs, current_study):
    study = scs.next_study(current_study)
    schedule(
        "end_study_delay",
        f"{study.id}, {scs.subject_id}",
        next_run=datetime.now() + scs.study_collection.inter_study_delay,
    )


def end_study_delay(study_id, subject_id):
    study = pm.Study.objects.get(id=study_id)
    subject = em.Subject.objects.get(id=subject_id)
    study.add_to_allowlist([subject.prolific_id])
    schedule(
        "prolific.tasks.study_warning",
        f"{scs.id}, {study_id}",
        next_run=datetime.now() + scs.study_time_to_warning,
    )


def study_warning(scs_id, study_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    study = pm.Study.objects.get(id=study_id)
    started = (
        em.Assignments.objects.filter(alt_id=study.remote_id)
        .exclude("not-started")
        .count()
    )
    if not started:
        api.send_message(
            scs.subject.prolific_id,
            latest_study_id,
            scs.study_collection.collection_warning_message,
        )
        schedule(
            "prolific.study_end_grace",
            f"{scs_id}, {study_id}",
            next_run=datetime.now() + scs.study_grace_interval,
        )


def studdy_end_grace(scs_id, study_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    study = pm.Study.objects.get(id=study_id)
    started = (
        em.Assignments.objects.filter(alt_id=study.remote_id)
        .exclude("not-started")
        .count()
    )
    if not started:
        study.remove_participant(scs.subject.prolific_id)


def collection_end_time_to_first_study(scs_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    first_study = scs.study_collection.study_set.order_by("rank")[0]
    if (
        em.Assignment.objects.filter(battery=first_study.battery)
        .exclude(status="not-started")
        .count()
        == 0
    ):
        first_study.remove_participant(study.prolific_id)
        api.send_message(
            scs.subject.prolific_id,
            latest_study_id,
            scs.study_collection.collection_warning_message,
        )


def collection_end_grace(scs_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    batteries = em.Battery.objects.filter(
        study__study_collection__id=scs.study_collection.id
    )
    studies = scs.study_collection.study_set.all()
    assignments = em.Assignment.objects.filter(
        subject=scs.subject, battery__in=batteries
    )
    completed = assignments.filter(status="completed").count() == batteries.count()

    if not completed:
        if scs.study_collection.collection_kick_on_timeout:
            for study in scs.study_collection.study_set.all():
                study.remove_participant(pid=scs.subject.prolific_id)
            scs.status = "kicked"
        else:
            scs.status = "flagged"
        scs.save()


def collection_warning(scs_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    scs.study_collection.study_set.order_by("rank")
    batteries = em.Battery.objects.filter(
        study__study_collection__id=scs.study_collection.id
    )
    battery_pks = batteries.values("pk").annotate(count=Count("id"))
    studies = scs.study_collection.study_set.all()
    assignments = em.Assignment.objects.filter(
        subject=scs.subject, battery__in=batteries
    )
    completed = assignments.filter(status="completed").count() == batteries.count()
    if not completed:
        schedule(
            "prolific.tasks.collection_end_grace",
            f"{scs_id}",
            next_run=datetime.now() + scs.collection_grace_interval,
        )
        # membership in first study is garunteed.
        first_study = scs.study_collection.study_set.order_by("rank")[0]
        api.send_message(
            scs.subject.prolific_id,
            latest_study_id,
            scs.study_collection.collection_warning_message,
        )
        scs.warned_at = datetime.now()
        scs.save()
