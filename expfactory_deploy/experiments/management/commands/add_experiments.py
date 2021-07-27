from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from experiments.models import ExperimentRepo
from experiments.utils.repo import find_new_experiments


class Command(BaseCommand):
    help = "Create experiment repo objects for new experiments"

    def add_arguments(self, parser):
        parser.add_argument(
            "repo_locations", nargs="+", type=lambda p: Path(p).absolute()
        )

    def handle(self, *args, **options):
        for repo_location in options["repo_locations"]:
            find_new_experiments(repo_location)
        self.stdout.write(self.style.SUCCESS("finished searching for experiments"))
