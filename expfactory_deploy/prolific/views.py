import json
import pprint

from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, F, Prefetch, Q
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
    FileResponse,
)
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, FormView, UpdateView

from experiments import views as exp_views
from experiments import models as exp_models

from prolific import models
from prolific import forms
from prolific import outgoing_api


class ProlificServe(exp_views.Serve):
    def set_subject(self):
        prolific_id = self.request.GET.get("PROLIFIC_PID", None)
        if prolific_id is None:
            self.subject = None
        else:
            self.subject = exp_models.Subject.objects.get_or_create(
                prolific_id=prolific_id
            )[0]

    """
    def complete(self, request):
        return redirect(reverse('prolific:complete', kwargs={'assignment_id': self.assignment.id}))
    """


class ProlificComplete(View):
    def get(self, request, *args, **kwargs):
        assignment = get_object_or_404(
            models.Assignment, id=self.kwargs.get("assignment_id")
        )
        cc_url = None
        try:
            cc = models.SimpleCC.objects.get(battery=assignment.battery)
            cc_url = cc.completion_url
        except ObjectDoesNotExist:
            pass

        return render(request, "prolific/complete.html", {"completion_url": cc_url})


class SimpleCCUpdate(LoginRequiredMixin, UpdateView):
    form_class = forms.SimpleCCForm
    template_name = "prolific/simplecc_form.html"

    def get_success_url(self):
        pk = self.kwargs.get("battery_id")
        return reverse("experiments:battery-detail", kwargs={"pk": pk})

    def get_object(self, queryset=None):
        return models.SimpleCC.objects.get_or_create(
            battery_id=self.kwargs.get("battery_id"), defaults={"completion_url": ""}
        )[0]


class StudyCollectionList(LoginRequiredMixin, ListView):
    model = models.StudyCollection
    queryset = models.StudyCollection.objects.prefetch_related(
        Prefetch("study_set", queryset=models.Study.objects.order_by("rank"))
    ).all()


class StudyCollectionView(LoginRequiredMixin, TemplateView):
    template_name = "prolific/study_collection.html"
    collection = None
    collection_kwargs = {}

    def get_object(self):
        collection_id = self.kwargs.get("collection_id")
        if collection_id is not None:
            self.collection = get_object_or_404(
                models.StudyCollection, pk=collection_id
            )
            self.collection_kwargs = {"instance": self.collection}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["collection_id"] = self.kwargs.get("collection_id")

        if "form" not in kwargs:
            context["form"] = forms.StudyCollectionForm(**self.collection_kwargs)
        else:
            context["form"] = kwargs.get("form")

        initial = []
        if self.collection:
            initial = list(
                models.Study.objects.filter(study_collection=self.collection).values(
                    "battery", "rank"
                )
            )
        if "study_rank_formset" not in kwargs:
            context["study_rank_formset"] = forms.BatteryRankFormset(initial=initial)
        else:
            context["study_rank_formset"] = kwargs.get("studyrankformset")

        context["batteries"] = exp_models.Battery.objects.exclude(
            status__in=["template", "inactive"]
        ).values_list("id", "title")

        return context

    def get(self, request, *args, **kwargs):
        self.get_object()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.get_object()
        form = forms.StudyCollectionForm(self.request.POST, **self.collection_kwargs)
        form.instance.user = request.user
        collection = form.save()

        study_rank_formset = forms.BatteryRankFormset(self.request.POST)

        if study_rank_formset.is_valid():
            study_set = list(collection.study_set.all())
            for i, form in enumerate(study_rank_formset):
                batt = form.cleaned_data["battery"]
                rank = form.cleaned_data["rank"]
                if i < len(study_set):
                    study_set[i].battery = batt
                    study_set[i].rank = rank
                    study_set[i].save()
                else:
                    new_study = models.Study(
                        battery=batt, rank=rank, study_collection=collection
                    )
                    new_study.save()
            [x.delete() for x in study_set[len(study_rank_formset) :]]
        else:
            print(study_rank_formset.errors)
            return self.render_to_response(
                self.get_context_data(form=form, study_rank_formset=study_rank_formset)
            )

        if form.is_valid():
            return HttpResponseRedirect(
                reverse_lazy(
                    "prolific:study-collection-update",
                    kwargs={"collection_id": collection.id},
                )
            )
        else:
            print(form.errors)
            return HttpResponseRedirect(
                reverse_lazy("prolific:study-collection-update")
            )


def fetch_studies_by_status(id=None):
    try:
        study_collection = models.StudyCollection.objects.get(id=id)
        response = outgoing_api.list_studies(study_collection.project)
    except (ObjectDoesNotExist, ValueError):
        response = outgoing_api.list_studies(id)
    studies_by_status = defaultdict(list)
    for study in response:
        studies_by_status[study["status"]].append(study)
    studies_by_status.default_factory = None
    return studies_by_status


def fetch_remote_study_details(id=None):
    study = outgoing_api.study_detail(id)
    participants = []
    for filter in study.get("filters", []):
        if filter.get("filter_id") == "participant_group_allowlist":
            for gid in filter.get("selected_values", []):
                response = outgoing_api.get_participants(gid)
                participants.extend(response.get("results", []))
    return {"study": study, "participants": participants}


@login_required
def remote_studies_list(request, id=None):
    try:
        study_collection = models.StudyCollection.objects.get(id=id)
    except (ObjectDoesNotExist, ValueError):
        study_collection = None

    studies_by_status = defaultdict(list)
    try:
        studies_by_status = fetch_studies_by_status(id=id)
    except Exception as e:
        messages.error(request, e)
    context = {
        "studies_by_status": studies_by_status,
        "study_collection": study_collection,
        "id": id,
    }
    return render(request, "prolific/remote_studies_list.html", context)


@login_required
def remote_study_detail(request, id=None):
    context = {}
    try:
        context = fetch_remote_study_details(id=id)
    except Exception as e:
        messages.error(request, e)

    return render(request, "prolific/remote_study_detail.html", context)


@login_required
def create_drafts_view(request, collection_id):
    collection = get_object_or_404(models.StudyCollection, id=collection_id)
    responses = []
    try:
        responses = collection.create_drafts()
    except Exception as e:
        messages.error(request, e)
    return render(
        request,
        "prolific/create_drafts_responses.html",
        {"responses": responses, "id": collection_id},
    )


@login_required
def publish_drafts(request, collection_id):
    studies = fetch_studies_by_status(collection_id)
    responses = []
    for study in studies.get("UNPUBLISHED"):
        try:
            response = outgoing_api.publish(study["id"])
            responses.append(response)
        except Exception as e:
            messages.error(request, e)

    return render(
        request,
        "prolific/create_drafts_responses.html",
        {"responses": responses, "id": collection_id},
    )


"""
    Summary and progress views
"""


@login_required
def collection_progress_alt(request, collection_id):
    context = {}
    context["collection"] = get_object_or_404(models.StudyCollection, id=collection_id)
    context["battery_results"] = (
        exp_models.Battery.objects.filter(study__study_collection=collection_id)
        .values("title")
        .annotate(completed=Count(Q(assignment__result__status="complete")))
        .order_by("study__rank")
    )
    return render(request, "prolific/collection_progress_alt.html", context)


@login_required
def collection_recently_completed(request, collection_id, days, by):
    collection = get_object_or_404(models.StudyCollection, id=collection_id)
    td = timezone.now() - timedelta(days=days)
    if by == "assignment":
        recent = exp_models.Assignment.objects.filter(
            battery__study__study_collection=collection_id
        ).annotate(prolific_id=F("subject__prolific_id"), parent=F("battery__title"))
    elif by == "result":
        recent = exp_models.Result.objects.filter(
            assignment__battery__study__study_collection=collection_id
        ).annotate(
            prolific_id=F("assignment__subject__prolific_id"),
            parent=F(
                "battery_experiment__experiment_instance__experiment_repo_id__name"
            ),
        )
    else:
        raise Http404("unsupported model")
    recent = recent.filter(completed_at__gte=td)
    return render(
        request,
        "prolific/collection_recently_completed.html",
        {"recent": recent, "td": td, "days": days, "collection": collection, "by": by},
    )


"""
    Display recent participants using the fields inside the subject model for last seen.
    A variant of this could live in experiments app. Only put here since we ignore any
    one without a prolific id and can filter on study_collections.
"""


@login_required
def recent_participants(request):
    collection_id = request.GET.get("collection_id", None)
    limit = int(request.GET.get("limit", None))
    context = {}
    subjects = (
        exp_models.Subject.objects.exclude(last_url_at=None)
        .exclude(prolific_id=None)
        .order_by("-last_url_at")
        .select_related()
    )
    if collection_id:
        context["collection"] = get_object_or_404(
            models.StudyCollection, id=collection_id
        )
        subjects = subjects.filter(
            assignment__battery__study__study_collection__id=collection_id
        )
    if limit:
        subjects = subjects[:limit]
    context["subjects"] = subjects
    return render(request, "prolific/recent_participants.html", context)


@login_required
def collection_progress(request, collection_id):
    collection = get_object_or_404(models.StudyCollection, id=collection_id)
    subjects = exp_models.Subject.objects.filter(
        studycollectionsubject__study_collection=collection
    )
    studies = collection.study_set.all().order_by("rank")

    subject_groups = {}
    errors = []

    for subject in subjects:
        subject_groups[subject] = {}
        for study in studies:
            completed = exp_models.Assignment.objects.filter(
                status="completed", subject=subject, battery=study.battery
            ).count()
            subject_groups[subject][study.battery.id] = {"completed": completed}

    for study in studies:
        if subjects.count() == 0:
            break
        try:
            details = fetch_remote_study_details(id=study.remote_id)
        except e:
            errors.append(f"Error on {study.remoteid}: {e}")
            continue
        for participant in details["participants"]:
            try:
                subject = subjects.get(prolific_id=participant["participant_id"])
                subject_groups[subject][study.battery.id]["date_added"] = participant[
                    "datetime_created"
                ]
            except ObjectDoesNotExist:
                subject_groups[subject][study.battery.id]["date_added"] = None

    context = {
        "subject_groups": subject_groups,
        "studies": studies,
        "subjects": subjects,
        "collection": collection,
        "errors": errors,
    }
    return render(request, "prolific/collection_progress.html", context)


"""
    Summary and progress views end
"""

"""
    Should probably exist as a method of the form itself.
    given a list of prolific Ids and study collection:
        - create Subject instances for PIDs if they don't exist.
        - create assignments if subject was created?
        - StudyCollectionSubject, permenatly links collection and pid.
            - What are we really doing with this model?
        - See what batteries subject has completed
            - find earliest incomplete in StudyCollection rank order.
            - via prolific api add them to partgroup/allowlist/etc...
"""


class ParticipantFormView(LoginRequiredMixin, FormView):
    template_name = "prolific/participant_form.html"
    form_class = forms.ParticipantIdForm
    success_url = reverse_lazy("prolific:study-collection-list")

    def form_valid(self, form):
        ids = form.cleaned_data["ids"]
        collection = get_object_or_404(
            models.StudyCollection, id=self.kwargs["collection_id"]
        )

        subjects = []
        for id in ids:
            subject, created = exp_models.Subject.objects.get_or_create(prolific_id=id)
            subjects.append(subject)

        for subject in subjects:
            (
                subject_collection,
                created,
            ) = models.StudyCollectionSubject.objects.get_or_create(
                study_collection=collection, subject=subject
            )

        pids_to_add = defaultdict(list)
        studies = models.Study.objects.filter(study_collection=collection).order_by(
            "rank"
        )
        # Only works with study in inner for loop, we only want to add each subject at most once to an allowlist in this call.
        for subject in subjects:
            for study in studies:
                completed = exp_models.Assignment.objects.filter(
                    status="completed", subject=subject, battery=study.battery
                )
                if len(completed) == 0:
                    pids_to_add[study.remote_id].append(subject.prolific_id)
                    break

        for study in studies:
            study.add_to_allowlist(pids_to_add[study.remote_id])

        return super().form_valid(form)


@login_required
def clear_remote_ids(request, collection_id):
    collection = get_object_or_404(models.StudyCollection, pk=collection_id)
    collection.clear_remote_ids()
    return HttpResponseRedirect(reverse_lazy("prolific:study-collection-list"))


@login_required
def toggle_collection(request, collection_id):
    collection = get_object_or_404(models.StudyCollection, pk=collection_id)
    collection.active = not collection.active
    collection.save()
    return HttpResponseRedirect(reverse_lazy("prolific:study-collection-list"))


class BlockedParticipantList(LoginRequiredMixin, ListView):
    model = models.BlockedParticipant


class BlockedParticipantUpdate(LoginRequiredMixin, UpdateView):
    model = models.BlockedParticipant
    fields = ["prolific_id", "active", "note"]
    success_url = reverse_lazy("prolific:blocked-participant-list")


class BlockedParticipantCreate(LoginRequiredMixin, CreateView):
    model = models.BlockedParticipant
    fields = ["prolific_id", "active", "note"]
    success_url = reverse_lazy("prolific:blocked-participant-list")
