from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

from guardian.shortcuts import assign_perm

'''
    Model to use for inheritance to have an object owner and an optional group.
    Also uses django guardian to automatically set owner change permissions.
'''
class OwnableModel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            content_type = ContentType.objects.get_for_model(self)
            change_perm = 'change_{0}'.format(content_type.model)
            assign_perm(change_perm, self.get[owner_field], self)

    class Meta:
        abstract = True
