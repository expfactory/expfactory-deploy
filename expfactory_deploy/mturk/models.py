import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from experiments.models import Battery, Subject
from users.models import Group

from mturk import boto_utils


# We aren't strict about auto creating assignments for subjects that start a
# battery, so we fk to battery and subject instead of just assignment.
class MturkPayment(models.Model):
    battery = models.ForeignKey(Battery, on_delete=models.DO_NOTHING)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    hit = models.TextField(blank=True)
    issued = models.DateField(blank=True, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    note = models.TextField(blank=True)


class MturkCredentials(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    name = models.TextField()
    file_name = models.TextField()

    def get_credentials(self):
        return None

    def get_client(self):
        return boto_utils.BotoWrapper(self.get_credentials())


class MturkApiOperation(models.Model):
    response = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)


# Group here is not an AWS term, using it to distiguish from HITTypes or HITLayouts
class HitGroup(models.Model):
    parent = models.ForeignKey(
        "HitGroup", on_delete=models.CASCADE, blank=True, null=True
    )
    credentials = models.ForeignKey(
        MturkCredentials, on_delete=models.CASCADE, blank=True, null=True
    )
    sandbox = models.BooleanField(default=True)
    battery = models.ForeignKey(
        Battery, on_delete=models.CASCADE, blank=True, null=True
    )
    details = models.ForeignKey("HitGroupDetails", on_delete=models.CASCADE, null=True)
    note = models.TextField(blank=True)
    published = models.DateTimeField(blank=True, null=True)
    number_of_assignments = models.IntegerField()

    def clone(self, battery=None):
        new_hit_group = self
        new_hit_group.pk = None
        new_hit_group.published = None
        new_hit_group.parent = self
        if battery:
            new_hit_group.battery = battery
        new_details = self.details
        new_details.pk = None
        new_details.save()
        new_hit_group.details = new_details
        new_hit_group.save()
        return new_hit_group

    def publish(self):
        if self.published:
            raise Exception("This hit group has already been published")
        if self.credentials:
            client = self.credentials.get_client()
        else:
            client = boto_utils.BotoWrapper()
        hit = self.details.to_hit_dict()
        url = f'https://0.0.0.0:8000{reverse("experiments:serve-battery", args=[self.battery.pk])}'
        client.create_hits_by_url(url, self.number_of_assignments, **hit)


class HitGroupDetails(models.Model):
    title = models.TextField()
    description = models.TextField()
    keywords = models.TextField(blank=True)
    reward = models.DecimalField(decimal_places=2, max_digits=10)
    auto_approval_delay = models.IntegerField(blank=True, null=True)
    lifetime_in_hours = models.IntegerField(default=168)
    assignment_duration_in_hours = models.IntegerField(default=168)
    qualification_requirements = models.JSONField(
        default=lambda: lambda: boto_utils.default_qualification
    )
    request_annotation = models.UUIDField(default=uuid.uuid4, editable=False)

    def to_hit_dict(self):
        hit = {
            "Title": self.title,
            "Description": self.description,
            "Keywords": self.keywords,
            "Reward": str(self.reward),
            "LifetimeInSeconds": self.lifetime_in_hours * 60 * 60,
            "AssignmentDurationInSeconds": self.assignment_duration_in_hours * 60 * 60,
            "QualificationRequirements": self.qualification_requirements,
            "RequesterAnnotation": str(self.request_annotation),
        }
        if self.auto_approval_delay:
            hit["AutoApprovalDelayInSeconds"] = self.auto_approval_delay
        return hit


class HitGroupHits(models.Model):
    hit_group = models.ForeignKey(HitGroup, on_delete=models.CASCADE)
    hit_id = models.TextField()
    unique_request_token = models.TextField(blank=True)


"""
  "Title": String,
  "Description": String,
  "Question": String,
  "Reward": String,
  "AssignmentDurationInSeconds": Integer,
  "LifetimeInSeconds": Integer,
  "Keywords": String,
  "MaxAssignments": Integer,
  "AutoApprovalDelayInSeconds": Integer,
  "QualificationRequirements": QualificationRequirementList,


  "HITLayoutId": String,
  "HITLayoutParameters": HITLayoutParameterList,
  "AssignmentReviewPolicy": ReviewPolicy,
  "HITReviewPolicy": ReviewPolicy,
  "RequesterAnnotation": String,
  "UniqueRequestToken": String
  """
