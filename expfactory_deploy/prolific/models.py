from collections import defaultdict
from datetime import datetime, timedelta
from uuid import uuid4

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.conf import settings

from experiments.models import Battery, Subject, Assignment
from prolific import outgoing_api as api
from pyrolific import models as api_models

from model_utils import Choices
from model_utils.models import TimeStampedModel
from model_utils.fields import StatusField, MonitorField

"""
Due to how prolific tracks time for payment we much chunk large batteries into
multiple batteries that can be done in single sittings.
"""


class StudyCollection(models.Model):
    name = models.TextField(blank=True, help_text="Name internal to expfactory.")
    project = models.TextField(
        blank=True, help_text="Prolific project ID for the studies to be created under."
    )
    workspace_id = models.TextField(blank=True)
    title = models.TextField(
        blank=True,
        help_text="Base Title to be used by all stutdies in collection on Prolific.",
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the study for the participants to read before starting the study.",
    )
    total_available_places = models.IntegerField(default=0)
    estimated_completion_time = models.IntegerField(
        default=0, help_text="Value in minutes."
    )
    reward = models.IntegerField(default=0, help_text="Value in cents.")
    published = models.BooleanField(default=False)
    inter_study_delay = models.DurationField(null=True, blank=True)
    active = models.BooleanField(default=True)
    number_of_groups = models.IntegerField(
        default=0,
        help_text="""
            Number of different groups to randomly assign participants to.
            A participants group number is injected into serve experiment template for use by experiments.
            0 means nothing will be added to the context.
        """,
    )
    parent = models.ForeignKey(
        "StudyCollection",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    time_to_start_first_study = models.DurationField(
        null=True,
        blank=True,
        help_text="hh:mm:ss - Upon adding participant to a study collection, they have this long to start the first study before being sent a warning message.",
    )
    failure_to_start_grace_interval = models.DurationField(
        null=True,
        default=timedelta(0),
        blank=True,
        help_text="hh:mm:ss - Time from previous warning to kick from study. If set to 0 nothing is done instead.",
    )
    failure_to_start_message = models.TextField(blank=True)
    failure_to_start_warning_message = models.TextField(blank=True)
    study_time_to_warning = models.DurationField(
        null=True,
        blank=True,
        help_text="hh:mm:ss - After completing a study participants will be reminded to start on the next study after this amount of time.",
    )
    study_warning_message = models.TextField(blank=True)
    study_grace_interval = models.DurationField(
        null=True,
        blank=True,
        help_text="hh:mm:ss - Time after warning message has been sent to kick participant from the study.",
    )
    study_kick_on_timeout = models.BooleanField(
        default=False,
        help_text="If True kick participant after a expiration of grace period if they have not started the study.",
    )
    collection_time_to_warning = models.DurationField(
        null=True,
        blank=True,
        help_text="hh:mm:ss - Overall time participant has to complete all studies before recieving a warning message.",
    )
    collection_warning_message = models.TextField(blank=True)
    collection_grace_interval = models.DurationField(
        null=True,
        blank=True,
        help_text="hh:mm:ss - Time after warning message is sent to kick participant from remaining studies.",
    )
    collection_kick_on_timeout = models.BooleanField(
        default=False,
        help_text="If True kick participant after the expiration of grace period from having not completed all studies.",
    )
    screener_for = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.SET_NULL
    )
    screener_rejection_message = models.TextField(blank=True)

    @property
    def study_count(self):
        return self.study_set.all().count()

    @property
    def deployed(self):
        return bool(self.study_set.exclude(remote_id="").count())

    def next_study(self, sid):
        studies = self.study_set.all().order_by("rank")
        prev = None
        for study in studies:
            if prev and prev.id == sid:
                return study
            prev = study
        return None

    def set_missing_group_indices(self):
        group_count = 1
        for scs in self.collection.studycollectionsubject_set.filter(group_index=0):
            scs.group_index = group_count % self.number_of_groups
            scs.save()
            group_count += 1

    def clear_remote_ids(self):
        for study in self.study_set.all():
            study.participant_group = ""
            study.remote_id = ""
            study.save()

    def create_drafts(self):
        studies = self.study_set.order_by("rank")
        study_responses = []
        if len(studies) < 1:
            return study_responses

        # api_studies = api.list_studies()

        id_to_set = None
        if not studies[0].participant_group:
            next_group = api.create_part_group(self.project, studies[0].part_group_name)
            id_to_set = next_group["id"]

        for i, study in enumerate(studies):
            if id_to_set:
                study.participant_group = id_to_set
                study.save()

            if i + 1 < len(studies):
                next_group = api.create_part_group(
                    self.project, studies[i + 1].part_group_name
                )
                next_id = next_group["id"]
                id_to_set = next_group["id"]
                print(id_to_set)
            else:
                next_id = None

            if self.inter_study_delay:
                next_id = None
            response = study.create_draft(next_id)

            study_responses.append(response)
            print(response)
        return study_responses

    def get_api_studies(self):
        studies = self.study_set.order_by("rank")
        study_responses = []
        if len(studies) < 1:
            return study_responses
        for study in studies:
            response = api.study_detail(id=study.remote_id)
            study_responses.append((study, response))
        return study_responses

    def set_allowlists(self):
        studies = list(self.study_set.order_by("rank"))
        blocked = BlockedParticipant.objects.filter(active=True).values("prolific_id")
        blocked = set([x["prolific_id"] for x in blocked])

        if len(studies) < 2:
            return
        study = studies[0]
        if not study.remote_id:
            # raise Exception("No study id")
            return
        if not study.participant_group:
            # raise Exception("No participant group")
            return
        response = api.get_participants(study.participant_group)

        to_promote = set([x["participant_id"] for x in response["results"]])

        to_promote = to_promote - blocked
        for study in studies:
            if len(to_promote) == 0:
                return
            if not study.remote_id:
                raise Exception("No study id")
            if not study.participant_group:
                raise Exception("No participant group")
            submissions = api.list_submissions(study.remote_id)
            submitted = set()
            for submission in submissions:
                pid = submission.get("participant_id")
                submitted.add(pid)
                to_promote.add(pid)
                completed_at = submission.get("completed_at")
                if not completed_at and pid in to_promote:
                    to_promote.remove(pid)
                completed_at = datetime.fromisoformat(completed_at)
                if (
                    completed_at
                    > datetime.now(completed_at.tzinfo) - self.inter_study_delay
                ):
                    to_promote.remove(pid)
            add_to_group = to_promote - submitted - blocked
            if len(add_to_group):
                study.add_to_allowlist(list(add_to_group))
            to_promote = to_promote - add_to_group - blocked
        return

    """
    https://github.com/rwblair/pyrolific/issues/3
    """

    def default_study_args(self, nested_actions=False):
        completion_code_kwargs = {
            "completion_code": "",
            "completion_code_action": "AUTOMATICALLY_APPROVE",
        }
        if nested_actions:
            completion_code_kwargs = {
                "completion_codes": [
                    {
                        "code": "",
                        "code_type": "COMPLETED",
                        "actions": [
                            {"action": "AUTOMATICALLY_APPROVE"},
                        ],
                    }
                ],
            }

        return {
            "name": self.title,
            "description": f"{self.description}",
            "prolific_id_option": "url_parameters",
            "completion_option": "code",
            "total_available_places": self.total_available_places,
            "estimated_completion_time": self.estimated_completion_time,
            "reward": self.reward,
            "device_compatibility": ["desktop"],
            **completion_code_kwargs,
        }


query_params = f"?{settings.PROLIFIC_PARTICIPANT_PARAM}={{{{%PROLIFIC_PID%}}}}&{settings.PROLIFIC_STUDY_PARAM}={{{{%STUDY_ID%}}}}&{settings.PROLIFIC_SESSION_PARAM}={{{{%SESSION_ID%}}}}"


def part_group_action(pid=""):
    return {"action": "ADD_TO_PARTICIPANT_GROUP", "participant_group": pid}


def default_allowlist(group_id=""):
    return {"filter_id": "participant_group_allowlist", "selected_values": [group_id]}


def default_previous_studies():
    return {"filter_id": "previous_studies_allowlist", "selected_values": []}


class Study(models.Model):
    battery = models.ForeignKey(Battery, null=True, on_delete=models.SET_NULL)
    study_collection = models.ForeignKey(
        StudyCollection, null=True, on_delete=models.SET_NULL
    )
    rank = models.IntegerField(
        default=0,
        verbose_name="Experiment order",
    )
    remote_id = models.TextField(blank=True)
    participant_group = models.TextField(blank=True)
    completion_code = models.TextField(blank=True)

    @property
    def part_group_name(self):
        return f"collection: {self.study_collection.id}, study: {self.id}, rank: {self.rank}, battery: {self.battery.title} (pg)"


    def __str__(self):
        return f'{self.battery.title} - prolific:{self.remote_id}'

    def set_group_name(self):
        if self.remote_id and self.participant_group:
            api.update_part_group(self.participant_group, self.part_group_name)

    def create_draft(self, next_group=None, dry_run=False):
        if self.remote_id and not dry_run:
            response = api.study_detail(id=self.remote_id)
            # check next_group here
            if not hasattr(response, "status_code"):
                return response

        study_args = self.study_collection.default_study_args(nested_actions=next_group)
        study_args[
            "name"
        ] = f"{study_args['name']} ({self.rank + 1} of {self.study_collection.study_count})"
        study_args[
            "external_study_url"
        ] = f"https://deploy.expfactory.org/prolific/serve/{self.battery.id}{query_params}"
        if self.completion_code == "":
            self.completion_code = str(uuid4())[:8]

        if next_group:
            study_args["completion_codes"][0]["code"] = self.completion_code
            study_args["completion_codes"][0]["code_type"] = "COMPLETED"
            study_args["completion_codes"][0]["actions"].append(
                part_group_action(next_group)
            )
        else:
            study_args["completion_code"] = self.completion_code

        if self.participant_group:
            study_args["filters"] = [default_allowlist(self.participant_group)]
        study_args["project"] = self.study_collection.project
        if dry_run:
            print(study_args)
            print("-------")
            print(api_models.CreateStudy.from_dict(study_args))
            return
        response = api.create_draft(study_args)
        if not hasattr(response, "status_code"):
            self.remote_id = response.get("id", None)
            self.save()
        return response

    def add_to_allowlist(self, pids):
        if not self.participant_group:
            # make new group
            return
        api.add_to_part_group(self.participant_group, pids)
        for pid in pids:
            if pid != None:
                subject, created = Subject.objects.get_or_create(prolific_id=pid)
                study_subject, ss_created = StudySubject.objects.get_or_create(
                    study=self, subject=subject
                )

    def remove_participant(self, pid):
        if not self.participant_group:
            return
        api.remove_from_part_group(self.participant_group, [pid])
        if pid != None:
            try:
                subject = Subject.objects.get(prolific_id=pid)
                study_subject = StudySubject.objects.get(
                    study=self, subject=subject
                ).delete()
            except ObjectDoesNotExist:
                return


class StudyRank(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    rank = models.IntegerField(
        default=0,
        verbose_name="Experiment order",
    )


class StudySubject(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, blank=True)
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, blank=True, null=True
    )
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, blank=True)
    assigned_to_study = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    STATUS = Choices(
        "n/a",
        "not-started",
        "started",
        "completed",
        "failed",
        "redo",
        "kicked",
        "flagged",
    )
    status = StatusField(choices_name="STATUS", default="n/a")
    failed_at = MonitorField(
        monitor="status", when=["kicked", "flagged", "failed"], default=None, null=True
    )
    warned_at = models.DateTimeField(default=None, blank=True, null=True)
    STATUS_REASON = Choices("n/a", "study-timer", "initial-timer", "collection-timer")
    status_reason = StatusField(choices_name="STATUS_REASON", default="n/a")
    prolific_session_id = models.TextField(blank=True, default="")
    added_to_study = models.DateTimeField(default=None, blank=True, null=True)

    """
    Maybe we should just set this as a foreign key. If we have a study collection subject and want all the study subjects we do something like:
    StudySubject.objects.filter(subject=my_sub, study__study_collection=scs.study_collection)
    """

    @property
    def study_collection_subject(self):
        if not self.study:
            return
        return StudyCollectionSubject.objects.get(
            study_collection=self.study.study_collection, subject=self.subject
        )

    def save(self, *args, **kwargs):
        if self.pk == None:
            assignments = Assignment.objects.filter(
                subject=self.subject,
                battery=self.study.battery,
                alt_id=self.study.remote_id,
            )
            if len(assignments) == 0:
                assignment = Assignment.objects.create(
                    subject=self.subject,
                    battery=self.study.battery,
                    alt_id=self.study.remote_id,
                )
                assignment.save()
                self.assignment = assignment
            elif len(assignments) == 1:
                self.assignment = assignments[0]
            else:
                # pray on what to do here. Choose one based on timestamp or status?
                self.assignment = assignments[0]
        super().save(*args, **kwargs)

    def get_prolific_status(self):
        if not self.prolific_session_id:
            return None
        response = api.get_submission(self.prolific_session_id)
        if hasattr(response, "status"):
            return response.status
        # how do we actually want to handle an error here?
        return None

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["study", "subject"], name="UniqueStudySubject"
            )
        ]


"""
class CollectionSubjectManager(models.Manager):
    def create_from_subjects(self, subjects, collection):
"""

"""
    ttfs - Timer To First Study
    ttcc - Timer To Complete Collection
"""


class StudyCollectionSubject(models.Model):
    study_collection = models.ForeignKey(StudyCollection, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    group_index = models.IntegerField(default=0)
    STATUS = Choices(
        "n/a",
        "not-started",
        "started",
        "completed",
        "failed",
        "redo",
        "kicked",
        "flagged",
    )
    status = StatusField(choices_name="STATUS", default="n/a")
    failed_at = MonitorField(
        monitor="status", when=["kicked", "failed"], default=None, null=True
    )
    warned_at = models.DateTimeField(default=None, blank=True, null=True)
    current_study = models.ForeignKey(
        Study, blank=True, null=True, on_delete=models.SET_NULL, default=None
    )
    STATUS_REASON = Choices("n/a", "study-timer", "initial-timer", "collection-timer")
    status_reason = StatusField(choices_name="STATUS_REASON", default="n/a")
    ttfs_warned_at = models.DateTimeField(default=None, blank=True, null=True)
    ttcc_warned_at = models.DateTimeField(default=None, blank=True, null=True)
    ttcc_flagged_at = MonitorField(
        monitor="status", when=["flagged"], default=None, null=True
    )
    active = models.BooleanField(default=True, help_text="Used to manually prevent subject from progressing in study.")

    @property
    def ended(self):
        return self.status in ["failed", "completed", "kicked"] or self.failed_at or not self.active

    """ Wonder how this works on a bulk create, potential for studycollcetionsubject_set.count
        to not give same number multiple times? Current use case is in a loop, should be fine.
    """

    def save(self, *args, **kwargs):
        number_of_groups = self.study_collection.number_of_groups
        if self.pk == None and number_of_groups > 0:
            current_part_count = (
                self.study_collection.studycollectionsubject_set.count()
            )
            self.group_index = (current_part_count + 1) % number_of_groups

        super().save(*args, **kwargs)

    def next_study(self, current_study):
        next_studies = (
            Study.objects.filter(study_collection=current_study.study_collection)
            .order_by("rank")
            .filter(rank__gt=current_study.rank)
        )
        if len(next_studies):
            return next_studies[0]
        return None

    def study_statuses(self):
        stCount = self.study_collection.study_set.count()
        stSubs = StudySubject.objects.filter(
            subject=self.subject, study__study_collection=self.study_collection
        )
        statuses = defaultdict(list)
        [statuses[x.assignment.status].append(x) for x in stSubs]
        return statuses

    """ If a participant times out, returns, or other fails to complete a study in prolific we
        have no simple way of 'reassigining' that study to them for another attempt.

        This function will create a new study collection for the subjects remaining batteries.
    """

    def incomplete_study_collection(self):
        old_id = self.study_collection.id
        study_collection = StudyCollection.objects.get(id=old_id)
        studies = list(study_collection.study_set.all().order_by("rank"))
        study_collection.pk = None
        study_collection.id = None
        study_collection.name = (
            f"Partial SC for {self.subject.prolific_id}: {study_collection.name}"
        )
        if not self.study_collection.parent:
            study_collection.parent = self.study_collection

        study_collection.save()
        new_scs = StudyCollectionSubject(
            subject=self.subject, study_collection=study_collection
        )
        new_scs.save()

        remaining_studies = []
        for study in studies:
            assignments = Assignment.objects.filter(
                subject=self.subject, battery=study.battery
            )
            if study.remote_id:
                with_alt = assignments.filter(alt_id=study.remote_id)
                if with_alt.count() > 0:
                    assignments = with_alt
            completed = assignments.filter(status="completed").count()
            if completed < 1:
                remaining_studies.append(study)

        studies = []
        api_responses = []
        new_rank = 0
        for study in remaining_studies:
            response = api.remove_from_part_group(
                study.participant_group, [self.subject.prolific_id]
            )
            api_responses.append(response)
            study.pk = None
            study.id = None
            study.remote_id = ""
            study.participant_group = ""
            study.study_collection = study_collection
            study.rank = new_rank
            new_rank += 1
            study.save()
            studies.append(study)
        responses = study_collection.create_drafts()
        api_responses.extend(responses)
        if len(studies) > 1:
            response = studies[0].add_to_allowlist([self.subject.prolific_id])
            api_responses.append(response)

        return api_responses, new_scs


class SimpleCC(TimeStampedModel):
    battery = models.OneToOneField(Battery, on_delete=models.CASCADE)
    completion_url = models.URLField(max_length=65536, blank=True)


class ProlificAPIResult(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    request = models.TextField(blank=True)
    response = models.JSONField()
    collection = models.ForeignKey(
        StudyCollection, on_delete=models.CASCADE, blank=True
    )


class BlockedParticipant(TimeStampedModel):
    prolific_id = models.TextField(unique=True)
    active = models.BooleanField(default=True)
    note = models.TextField(blank=True)


