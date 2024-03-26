from prolific import models as models

"""
    Copied from prolific.views.ParticipantFormView.form_valid.
    form_valid's code should be relaced with call to this.
"""


def add_subjects_to_collection(subjects, collection):
    from prolific.tasks import on_add_to_collection
    first_study = collection.study_set.first()
    for subject in subjects:
        (
            subject_collection,
            created,
        ) = models.StudyCollectionSubject.objects.get_or_create(
            study_collection=collection, subject=subject
        )
        if first_study:
            study_subject, created = models.StudySubject.objects.get_or_create(
                study=first_study, subject=subject
            )
        print(f"first study: {first_study}, ss.study: {study_subject.study}")
        if created:
            on_add_to_collection(subject_collection)
        if first_study and created:
            subject_collection.current_study = first_study

    ids = [x.prolific_id for x in subjects]
    if first_study:
        print(f"calling add to allow on {first_study.id} with pids: {ids}")
        first_study.add_to_allowlist(ids)
