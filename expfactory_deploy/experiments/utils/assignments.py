from django.conf import settings
from django.urls import reverse

from experiments import models as models

def batch_assignments(battery, num_subjects=1):
    urls = []
    for i in range(num_subjects):
        subject = models.Subject()
        subject.save()
        assignment = models.Assignment(subject=subject, battery=battery)
        assignment.save()
        urls.append(f'{settings.BASE_URL}{reverse("experiments:serve-battery", args=[subject.pk, battery.pk])}')
    return urls
