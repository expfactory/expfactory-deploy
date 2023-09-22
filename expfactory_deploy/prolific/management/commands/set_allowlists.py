from django.core.management.base import BaseCommand, CommandError
from prolific.models import StudyCollection


class Command(BaseCommand):
    help = "Promote subjects to next study in collection"

    def handle(self, *args, **options):
        collections = StudyCollection.objects.exclude(project='')
        for collection in collections:
            if len(collection.study_set.filter(remote_id='')):
                self.stdout.write(f"study collection {collection.id} has collections with no remote_id")
                continue
            collection.set_allowlists()
