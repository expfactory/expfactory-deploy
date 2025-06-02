from datetime import datetime, timedelta

from django.db.models import Count

from experiments import models as em
from prolific import models as pm
from prolific import outgoing_api as api
from prolific.utils import add_subjects_to_collection

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


# task friendly wrapper for the utility function
def add_to_collection(subject_id, collection_id, group_index=None):
    subject = em.Subject.objects.get(id=subject_id)
    collection = pm.StudyCollection.objects.get(id=collection_id)
    add_subjects_to_collection([subject], collection, group_index)


def on_complete_battery(sc, current_study, subject_id):
    study = sc.next_study(current_study)
    delay = sc.inter_study_delay if sc.inter_study_delay is not None else timedelta(0)
    subject = em.Subject.objects.get(id=subject_id)
    ss = pm.StudySubject.objects.get(study=current_study, subject=subject)
    scs = ss.study_collection_subject
    if ss.status == "kicked" or scs.status == "kicked":
        print(
            f"subject {ss.subject.id} listed as kicked on collection {scs.study_collection.id}"
        )
        return
    ss.status = "completed"
    ss.save()

    if study and not scs.ended:
        schedule(
            "prolific.tasks.end_study_delay",
            study.id,
            subject_id,
            next_run=datetime.now() + delay,
        )
    else:
        # is there really no next study?
        scs.status = "completed"
        scs.save()
        if scs.study_collection.screener_for is not None:
            pass_check = ss.assignment.pass_check()
            print(ss.id)
            print(ss.assignment.id)
            print(f"pass_check {pass_check}")
            if pass_check:
                group_index = None
                if (
                    scs.study_collection.number_of_groups > 0
                    and scs.study_collection.number_of_groups
                    == scs.study_collection.screener_for.number_of_groups
                ):
                    group_index = scs.group_index
                schedule(
                    "prolific.tasks.add_to_collection",
                    scs.subject.id,
                    scs.study_collection.screener_for.id,
                    group_index,
                    next_run=datetime.now() + scs.study_collection.inter_study_delay,
                )
            else:
                screener_rejection_message = (
                    scs.study_collection.screener_rejection_message
                )
                if screener_rejection_message:
                    api.send_message(
                        scs.subject.prolific_id,
                        ss.study.remote_id,
                        screener_rejection_message,
                    )


"""
    This is the inter-study delay, we want subjects to wait before starting next study.
"""


def end_study_delay(study_id, subject_id):
    study = pm.Study.objects.get(id=study_id)
    subject = em.Subject.objects.get(id=subject_id)
    study_subject, created = pm.StudySubject.objects.get_or_create(
        study=study, subject=subject
    )
    sc = study.study_collection
    scs = pm.StudyCollectionSubject.objects.get(subject=subject, study_collection=sc)
    if scs.ended:
        return
    scs.current_study = study
    scs.save()
    study.add_to_allowlist([subject.prolific_id])

    if sc.study_time_to_warning and sc.study_time_to_warning > timedelta(0):
        schedule(
            "prolific.tasks.study_warning",
            scs.id,
            study_id,
            next_run=datetime.now() + sc.study_time_to_warning,
        )


"""
    Any study must be started within a certain amount of time.
"""


def study_warning(scs_id, study_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    if scs.ended:
        return f"study collection subject {scs.id} listed as ended. Bailing on task"
    sc = scs.study_collection
    study = pm.Study.objects.get(id=study_id)
    started = (
        em.Assignment.objects.filter(alt_id=study.remote_id, subject=scs.subject)
        .exclude(status="not-started")
        .count()
    )
    if not started:
        study_subject = pm.StudySubject.objects.get(study=study, subject=scs.subject)
        api.send_message(
            scs.subject.prolific_id,
            study_id,
            sc.study_warning_message,
        )
        study_subject.warned_at = datetime.now()
        study_subject.save()
        if sc.study_grace_interval is not None and sc.study_grace_interval > timedelta(
            0
        ):
            schedule(
                "prolific.tasks.study_end_grace",
                scs_id,
                study_id,
                next_run=datetime.now() + sc.study_grace_interval,
            )
        return f"study collection subject {scs_id} not started"
    return f"study collection subject {scs_id} has started, no warnings issued"


def study_end_grace(scs_id, study_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    if scs.ended:
        return f"study collection subject {scs.id} listed as ended. Bailing on task"
    study = pm.Study.objects.get(id=study_id)
    ss = pm.StudySubject.objects.get(subject=scs.subject, study__id=study_id)
    started = ss.assignment.status != "not-started"
    if started:
        return f"{scs.subject} has started {study} taking no action"

    if scs.study_collection.study_kick_on_timeout:
        status = "kicked"
        study.remove_participant(scs.subject.prolific_id)
        message = f"removed ${scs.subject.prolific_id} from ${study} for not starting battery on time"
    else:
        status = "flagged"
        message = f"flagged ${scs.subject.prolific_id} from ${study} for not starting battery on time"

    ss.status = status
    ss.status_reason = "study-timer"
    scs.status = status
    scs.status_reason = "study-timer"
    ss.save()
    scs.save()
    return message


"""
    These are special for the first study a participant must start.
"""


def initial_end_grace(ss_id):
    ss = pm.StudySubject.objects.get(id=ss_id)
    scs = ss.study_collection_subject
    if scs.ended:
        return f"study collection subject {scs.id} listed as ended. Bailing on task"

    if ss.assignment.status != "not-started":
        return f"{ss.subject} started {ss.study} before time to first study grace ended"

    if scs.study_collection.failure_to_start_message:
        api.send_message(
            scs.subject.prolific_id,
            ss.study.remote_id,
            scs.study_collection.failure_to_start_message,
        )
    ss.study.remove_participant(ss.subject.prolific_id)
    ss.status = "kicked"
    ss.status_reason = "initial-timer"
    ss.save()
    scs.status = "kicked"
    scs.status_reason = "initial-timer"
    scs.save()
    return f"removed {scs.subject.prolific_id} from {scs.study_collection}. Failed to start first battery on time"


def initial_warning(ss_id):
    ss = pm.StudySubject.objects.get(id=ss_id)
    scs = ss.study_collection_subject
    if ss.study_collection_subject.ended:
        return f"{ss.subject} listed as having failed collection {ss.study_collection_subject.id}"
    if ss.assignment.status != "not-started":
        return f"{ss.subject} started {ss.study} before time to first study"

    if ss.study.study_collection.failure_to_start_warning_message:
        api.send_message(
            ss.subject.prolific_id,
            ss.study.remote_id,
            ss.study.study_collection.failure_to_start_warning_message,
        )
        warned_at = datetime.now()
        ss.warned_at = warned_at
        ss.save()
        scs.ttfs_warned_at = warned_at
        scs.save()

    if ss.study.study_collection.failure_to_start_grace_interval > timedelta(0):
        schedule(
            "prolific.tasks.initial_end_grace",
            ss_id,
            next_run=datetime.now()
            + ss.study.study_collection.failure_to_start_grace_interval,
        )
    return f"{ss.subject} has not started {ss.study} before time to first study"


"""
    There is an absolute max amount of time a subject can take to complete all studies.
"""


def collection_end_grace(scs_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    if scs.ended:
        return f"study collection subject {scs.id} listed as ended. Bailing on task"
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
            scs.status_reason = "collection-timer"
        else:
            scs.status = "flagged"
            scs.status_reason = "collection-timer"
        scs.save()
        return f"subject {scs.subject.id} set to {scs.status} for study collection {scs.study_collection.id}"
    return f"subject {scs.subject.id} completed batteries of study collection {scs.study_collection.id}"


def collection_warning(scs_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    if scs.ended:
        return f"study collection subject {scs.id} listed as ended. Bailing on task"
    batteries = em.Battery.objects.filter(
        study__study_collection__id=scs.study_collection.id
    )
    # battery_pks = batteries.values("pk").annotate(count=Count("id"))
    studies = scs.study_collection.study_set.all().order_by("rank")
    assignments = em.Assignment.objects.filter(
        subject=scs.subject, battery__in=batteries
    )
    completed = assignments.filter(status="completed").count() == batteries.count()
    if not completed:
        if (
            scs.study_collection.collection_grace_interval is not None
            and scs.study_collection.collection_grace_interval > timedelta(0)
        ):
            schedule(
                "prolific.tasks.collection_end_grace",
                f"{scs_id}",
                next_run=datetime.now()
                + scs.study_collection.collection_grace_interval,
            )
        # membership in first study is garunteed.
        if scs.current_study:
            study = scs.current_study
        else:
            study = scs.study_collection.study_set.order_by("rank").first()

        if scs.study_collection.collection_warning_message:
            api.send_message(
                scs.subject.prolific_id,
                study.remote_id,
                scs.study_collection.collection_warning_message,
            )
        scs.warned_at = datetime.now()
        scs.ttcc_warned_at = datetime.now()
        scs.save()
        return (
            f"warned subject {scs.subject.id} for collection {scs.study_collection.id}"
        )
    return f"subject {scs.subject.id} completed collection {scs.study_collection.id} - not warned"


def on_add_to_collection(scs):
    if scs.ended:
        print(
            "trying to add {scs.subject.id} to an ended collection {scs.study_collection.id }"
        )
        return
    sc = scs.study_collection
    ss = pm.StudySubject.objects.get(
        subject=scs.subject, study=sc.study_set.order_by("rank").first()
    )
    if not scs.current_study:
        scs.current_study = ss.study
        scs.save()
    else:
        print(f"subject {scs.subject.id} has current study. Not creating new timers")
        return
    if (
        sc.time_to_start_first_study is not None
        and sc.time_to_start_first_study > timedelta(0)
    ):
        schedule(
            "prolific.tasks.initial_warning",
            ss.id,
            next_run=datetime.now() + sc.time_to_start_first_study,
        )
    if (
        sc.collection_time_to_warning is not None
        and sc.collection_time_to_warning > timedelta(0)
    ):
        schedule(
            "prolific.tasks.collection_warning",
            scs.id,
            next_run=datetime.now() + sc.collection_time_to_warning,
        )
