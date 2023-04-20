from django.conf import settings
from django.db import models

from experiments.models import Battery, Subject
from users.models import Group

# We aren't strict about auto creating assignments for subjects that start a
# battery, so we fk to battery and subject instead of just assignment.
'''
class MturkPayment(models.Model):
    battery = models.ForeignKey(Battery)
    subject = models.ForeignKey(Subject)
    hit = models.TextField(blank=True)
    issued = models.DateField(blank=True, null=True)
    amount = models.DecimalField()
    note = models.TextField(blank=True)

class MturkCredentials(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    name = models.TextField()
'''
