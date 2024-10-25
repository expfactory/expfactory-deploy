import ast
import json
import math
import pandas

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Exists, F, OuterRef

from prolific import models as pm
from experiments import models as em
from analysis.models import ResultQA
from analysis.default_qa import apply_qa_funcs


class Command(BaseCommand):
    help = "Run QA for Results of study/battery/collection"

    def add_arguments(self, parser):
        parser.add_argument("ids", nargs="+", type=int)

    def handle(self, *args, **options):
        for id in options["ids"]:
            pass
            # pm.StudyCollection.objects
            # ResultQA.objects.filter


def study_collection_qa(id, rerun=False):
    results_qs = em.Result.objects.filter(
        subject__studycollectionsubject__study_collection=id
    )

    run_qa(results_qs, rerun)


def run_qa(results, rerun=False):
    import numpy as np
    if rerun is False:
        results = results.filter(
            ~Exists(ResultQA.objects.filter(exp_result=OuterRef("pk")))
        )

    results = results.annotate(
        task_name=F("battery_experiment__experiment_instance__experiment_repo_id__name")
    )

    for result in results:
        data = ast.literal_eval(result.data)
        if "trialdata" not in data:
            continue
        trialdata = data["trialdata"]
        if type(trialdata) == str:
            task_data = pandas.DataFrame(json.loads(trialdata))
        else:
            task_data = pandas.DataFrame(trialdata)
        task_name = result.task_name
        metrics, feedback, error = apply_qa_funcs(task_name, task_data)

        if metrics != None:
            for key in metrics:
                if type(metrics[key]) is str:
                    try:
                        metrics[key] = json.loads(metrics[key])
                    except json.decoder.JSONDecodeError:
                        continue
                if metrics[key] is None:
                    continue
                try:
                    if math.isnan(metrics[key]):
                        metrics[key] = None
                    elif isinstance(metrics[key], np.integer):
                        metrics[key] = int(metrics[key])
                    elif isinstance(metrics[key], np.float_):
                        metrics[key] = float(metrics[key])
                except TypeError:
                    continue

        ResultQA.objects.update_or_create(
            exp_result=result,
            defaults={"qa_result": metrics, "error": error, "feedback": feedback},
        )
