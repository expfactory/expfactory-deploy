from django.core.management.base import BaseCommand, CommandError
from django.db.models import Exists, F

from prolific import models as pm
from experiments import models as em
from analysis.models import ResultQA
from analysis.default_qa import appy_qa_funcs


class Command(BaseCommand):
    help = "Run QA for Results of study/battery/collection"

    def add_arguments(self, parser):
        parser.add_argument("ids", nargs="+", type=int)

    def handle(self, *args, **options):
        for id in options["ids"]:
            pass
            # pm.StudyCollection.objects
            # ResultQA.objects.filter


def run_qa(id):
    results = (
        Result.objects.filter(subject__studycollectionsubject__study_collection=id)
        .filter(~Exists(ResultQA.objects.filter(exp_result=OuterRef("pk"))))
        .annotate(
            task_name=F(
                "battery_experiment__experiment_instance__experiment_repo_id__name"
            )
        )
    )
    for result in results:
        metrics, error = apply_qa_funcs(result.task_name, result.data)
        ResultQA(exp_result=result, qa_result=metrics, error=error).save()
