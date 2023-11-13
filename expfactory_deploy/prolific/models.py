from datetime import datetime, timedelta
from uuid import uuid4

from django.db import models

from experiments.models import Battery, Subject, Assignment
from model_utils.models import TimeStampedModel
from prolific import outgoing_api as api
from pyrolific import models as api_models

'''
Due to how prolific tracks time for payment we much chunk large batteries into
multiple batteries that can be done in single sittings.
'''
class StudyCollection(models.Model):
    name = models.TextField(blank=True, help_text="Name internal to expfactory.")
    project = models.TextField(blank=True, help_text="Prolific project ID for the studies to be created under.")
    workspace_id = models.TextField(blank=True)
    title = models.TextField(blank=True, help_text="Base Title to be used by all stutdies in collection on Prolific.")
    description = models.TextField(blank=True)
    total_available_places = models.IntegerField(default=0)
    estimated_completion_time = models.IntegerField(default=0, help_text="Value in minutes.")
    reward = models.IntegerField(default=0, help_text="Value in cents.")
    published = models.BooleanField(default=False)
    inter_study_delay = models.DurationField(null=True, blank=True)
    active = models.BooleanField(default=True)

    @property
    def study_count(self):
        return self.study_set.all().count()

    def clear_remote_ids(self):
        for study in self.study_set.all():
            study.participant_group = ""
            study.remote_id = ""
            study.save()

    def create_drafts(self):
        studies = self.study_set.order_by('rank')
        study_responses = []
        if len(studies) < 1:
            return study_responses

        # api_studies = api.list_studies()

        id_to_set = None
        if not studies[0].participant_group:
            next_group = api.create_part_group(self.project, studies[0].part_group_name)
            id_to_set = next_group['id']

        for i, study in enumerate(studies):
            if (id_to_set):
                study.participant_group = id_to_set
                study.save()

            if (i + 1 < len(studies)):
                next_group = api.create_part_group(self.project, studies[i + 1].part_group_name)
                next_id = next_group['id']
                id_to_set = next_group['id']
                print(id_to_set)
            else:
                next_id = None

            if (self.inter_study_delay):
                next_id = None
            response = study.create_draft(next_id)

            study_responses.append(response)
            print(response)
        return study_responses

    def get_api_studies(self):
        studies = self.study_set.order_by('rank')
        study_responses = []
        if len(studies) < 1:
            return study_responses
        for study in studies:
            response = api.study_detail(id=study.remote_id)
            study_responses.append((study, response))
        return study_responses


    def set_allowlists(self):
        studies = list(self.study_set.order_by('rank'))
        blocked = BlockedParticipant.objects.filter(active=True).values('prolific_id')
        blocked = set([x['prolific_id'] for x in blocked])

        if len(studies) < 2:
            return
        study = studies[0]
        if not study.remote_id:
            raise Exception("No study id")
        if not study.participant_group:
            raise Exception("No participant group")
        response = api.get_participants(study.participant_group)

        to_promote = set([x['participant_id'] for x in response['results']])

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
                completed_at = submission.get('completed_at')
                if not completed_at and pid in to_promote:
                    to_promote.remove(pid)
                completed_at = datetime.fromisoformat(completed_at)
                if completed_at > datetime.now(completed_at.tzinfo) - self.inter_study_delay:
                    to_promote.remove(pid)
            add_to_group = to_promote - submitted - blocked
            if (len(add_to_group)):
                api.add_to_part_group(study.participant_group, list(add_to_group))
            to_promote = to_promote - add_to_group - blocked
        return

    def default_study_args(self):
        return {
            "name": self.title,
            "description": f"{self.description}",
            "prolific_id_option": "url_parameters",
            "completion_option": "code",
            "completion_codes": [
                {
                    "code": "",
                    "code_type": "COMPLETED",
                    "actions": [ {"action": "AUTOMATICALLY_APPROVE"}, ],
                }
            ],
            "total_available_places": self.total_available_places,
            "estimated_completion_time": self.estimated_completion_time,
            "reward": self.reward,
            "device_compatibility": ["desktop"],
        }

query_params = "?participant={{%PROLIFIC_PID%}},study={{%STUDY_ID%}},session={{%SESSION_ID%}}"

def part_group_action(pid=""):
    return {
        "action": "ADD_TO_PARTICIPANT_GROUP",
        "participant_group": pid
    }

def default_allowlist(group_id=""):
    return {
        "filter_id": "participant_group_allowlist",
        "selected_values": [ group_id ]
    }

def default_previous_studies():
    return {"filter_id": "previous_studies_allowlist", "selected_values": []}

class Study(models.Model):
    battery = models.ForeignKey(Battery, null=True, on_delete=models.SET_NULL)
    study_collection = models.ForeignKey(StudyCollection, null=True, on_delete=models.SET_NULL)
    rank = models.IntegerField(
        default=0,
        verbose_name="Experiment order",
    )
    remote_id = models.TextField(blank=True)
    participant_group = models.TextField(blank=True)
    completion_code = models.TextField(blank=True)

    @property
    def part_group_name(self):
        return f'collection: {self.study_collection.id}, study: {self.id}, rank: {self.rank}, battery: {self.battery.title} (pg)'

    def set_group_name(self):
        if self.remote_id and self.participant_group:
            api.update_part_group(self.participant_group, self.part_group_name)

    def create_draft(self, next_group=None, dry_run=False):
        if self.remote_id and not dry_run:
            response = api.study_detail(id=self.remote_id)
            # check next_group here
            if not hasattr(response, 'status_code'):
                return response

        study_args = self.study_collection.default_study_args()
        study_args['name'] = f"{study_args['name']} ({self.rank + 1} of {self.study_collection.study_count})"
        study_args['external_study_url'] = f"https://deploy.expfactory.org/{self.battery.id}/{query_params}"
        if self.completion_code == "":
            self.completion_code = str(uuid4())[:8]
        study_args['completion_codes'][0]['code'] = self.completion_code

        if (next_group):
            study_args['completion_codes'][0]['code_type'] = "COMPLETED"
            study_args['completion_codes'][0]['actions'].append(part_group_action(next_group))

        if self.participant_group:
            study_args['filters'] = [default_allowlist(self.participant_group)]
        study_args['project'] = self.study_collection.project
        if dry_run:
            print(study_args)
            print('-------')
            print(api_models.CreateStudy.from_dict(study_args))
            return
        response = api.create_draft(study_args)
        if not hasattr(response, 'status_code'):
            self.remote_id = response.get('id', None)
            self.save()
        return response

    def add_to_allowlist(self, pids):
        if (not self.participant_group):
            # make new group
            return
        api.add_to_part_group(self.participant_group, pids)

class StudyRank(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    rank = models.IntegerField(
        default=0,
        verbose_name="Experiment order",
    )

class StudySubject(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    # or subject? can get at all the information through the relations one way or another

    def result_qa(self):
        return

'''
class CollectionSubjectManager(models.Manager):
    def create_from_subjects(self, subjects, collection):
'''

class StudyCollectionSubject(models.Model):
    study_collection = models.ForeignKey(StudyCollection, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)


class SimpleCC(TimeStampedModel):
    battery = models.OneToOneField(Battery, on_delete=models.CASCADE)
    completion_url = models.URLField(max_length=65536, blank=True)

class ProlificAPIResult(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    request = models.TextField(blank=True)
    response = models.JSONField()
    collection = models.ForeignKey(StudyCollection, on_delete=models.CASCADE, blank=True)

class BlockedParticipant(TimeStampedModel):
    prolific_id = models.TextField(unique=True)
    active = models.BooleanField(default=True)
    note = models.TextField(blank=True)
