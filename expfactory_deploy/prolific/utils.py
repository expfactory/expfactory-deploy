from prolific import models as models

"""
    Copied from prolific.views.ParticipantFormView.form_valid.
    form_valid's code should be relaced with call to this.
"""


def add_subjects_to_collection(subjects, collection, group_index=None):
    from prolific.tasks import on_add_to_collection
    first_study = collection.study_set.order_by("rank").first()
    for subject in subjects:
        (
            subject_collection,
            scs_created,
        ) = models.StudyCollectionSubject.objects.get_or_create(
            study_collection=collection, subject=subject
        )
        if first_study:
            study_subject, ss_created = models.StudySubject.objects.get_or_create(
                study=first_study, subject=subject
            )
        print(f"first study: {first_study}, ss.study: {study_subject.study}")
        if scs_created:
            if group_index:
                subject_collection.group_index = group_index
                subject_collection.save()
            on_add_to_collection(subject_collection)
        if first_study and scs_created:
            subject_collection.current_study = first_study

    ids = [x.prolific_id for x in subjects]
    if first_study:
        print(f"calling add to allow on {first_study.id} with pids: {ids}")
        first_study.add_to_allowlist(ids)
