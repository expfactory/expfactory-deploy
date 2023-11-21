from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy

from analysis import models
from analysis.management.commands.run_qa import study_collection_qa
from prolific import models as pro_models
from experiments import models as exp_models


@login_required
def qa_by_sc(request, id):
    collection = get_object_or_404(pro_models.StudyCollection, id=id)
    results = (
        models.ResultQA.objects.filter(
            exp_result__battery_experiment__battery__study__study_collection__id=id
        )
        .annotate(
            subject_id=F("exp_result__assignment__subject__id"),
            prolific_id=F("exp_result__assignment__subject__prolific_id"),
            battery_name=F("exp_result__assignment__battery__title"),
            exp_name=F(
                "exp_result__battery_experiment__experiment_instance__experiment_repo_id__name"
            ),
        )
        .order_by("exp_result__battery_experiment__battery__study__rank")
    )

    return render(request, "analysis/qa_by_sc.html", {"results": results, "collection": collection})


@login_required
def trigger_qa_by_sc(request, id, rerun):
    study_collection_qa(id, rerun)
    return redirect(reverse("analysis:qa-by-sc", kwargs={"id": id}))
