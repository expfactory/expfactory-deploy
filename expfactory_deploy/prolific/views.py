import json
import pprint

from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
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

from prolific.tasks import on_add_to_collection

"""
    subclass of experiments app serve class view to handle query params from prolific.
    One issue here is that the query param keys are hard coded here and in prolific.models query_params.
"""


class ProlificServe(exp_views.Serve):
    def set_subject(self):
        part_param = settings.PROLIFIC_PARTICIPANT_PARAM
        prolific_id = self.request.GET.get(part_param, None)
        if prolific_id is None:
            self.subject = None
        else:
            self.subject = exp_models.Subject.objects.get_or_create(
                prolific_id=prolific_id
            )[0]

    """
        With the addition of StudySubject the question is should we ever need
        to create an assignment at this step?
    """

    def set_assignment(self):
        study_id = self.request.GET.get(settings.PROLIFIC_STUDY_PARAM, None)
        session_id = self.request.GET.get(settings.PROLIFIC_SESSION_PARAM, None)
        study_subjects = models.StudySubject.objects.filter(subject=self.subject)
        if study_id:
            study_subjects = study_subjects.filter(study__remote_id=study_id)
        if session_id:
            session_ss = study_subjects.filter(prolific_session_id=study_id)
            if len(session_ss):
                study_subjects = session_ss

        if len(study_subjects) > 1:
            pass

        if len(study_subjects):
            ss = study_subjects[0]
            self.assignment = ss.assignment
            if ss.prolific_session_id == None:
                ss.prolific_session_id = session_id
                ss.save()


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
            messages.success(request, "Study Collection saved")
            return HttpResponseRedirect(
                reverse_lazy(
                    "prolific:study-collection-update",
                    kwargs={"collection_id": collection.id},
                )
            )
        else:
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
    for filter in getattr(study, "filters", []):
        if getattr(filter, "filter_id", "") == "participant_group_allowlist":
            for gid in getattr(filter, "selected_values", []):
                response = outgoing_api.get_participants(gid)
                participants.extend(getattr(response, "results", []))
    return {"study": study, "participants": participants}


@login_required
def remote_studies_by_project(request, project_id):
    studies_by_status = defaultdict(list)
    try:
        studies_by_status = fetch_studies_by_status(id=project_id)
    except Exception as e:
        messages.error(request, e)


@login_required
def remote_studies_list(request, collection_id=None):
    try:
        study_collection = models.StudyCollection.objects.get(id=collection_id)
    except (ObjectDoesNotExist, ValueError):
        study_collection = None

    studies_in_db = list(
        models.Study.objects.filter(study_collection=study_collection).prefetch_related(
            "battery"
        )
    )
    sc_study_count = len(studies_in_db)
    tracked_remote_ids = [study.remote_id for study in studies_in_db if study.remote_id]

    studies_by_status = defaultdict(list)

    study_collection_subjects = models.StudyCollectionSubject.objects.filter(
        study_collection=study_collection
    ).prefetch_related("subject")

    for study_id in tracked_remote_ids:
        try:
            api_study = fetch_remote_study_details(id=study_id)
            api_study = api_study["study"]
            studies_by_status[api_study["status"]].append(api_study)
        except Exception as e:
            print(e)
            messages.error(request, e)

    publish = False
    draft = False
    add_parts = False
    bad_state = False
    if len(tracked_remote_ids) == 0:
        draft = True
        publish = False

        state_description = "There are no ids for prolific studies being tracked in the database. 'Create Drafts' will attempt to create a study on prolific for each battery in the current study collection."
    elif "ACTIVE" in studies_by_status and len(studies_by_status["ACTIVE"]) == len(
        tracked_remote_ids
    ):
        draft = False
        publish = False
        add_parts = True

        state_description = "All of the study ids being tracked in the database for this study collection are listed as 'active' on Prolific. Any participants added to the study collection should be able to access the studies on prolific as they become eligible (ex: interstudy delay)."
    elif "UNPUBLISHED" in studies_by_status and len(
        studies_by_status["UNPUBLISHED"]
    ) == len(tracked_remote_ids):
        draft = False
        publish = True
        add_parts = True

        state_description = "All of the study ids being tracked in the database exist as drafts on prolific's website but have not been published there. Until they are published they will be hidden from participants regardless of the participants association to the study collection listed here."

    elif "COMPLETED" in studies_by_status and len(
        studies_by_status["COMPLETED"]
    ) == len(tracked_remote_ids):
        state_description = "Collection for studies on prolific has completed. If you need to collect data for more participants use the 'clear remote ids' on the study colleciton list page to reset the databses state to not track any prolific study ids. From there drafts will need to be created, published and participants added."

    else:
        bad_state = True

        state_description = "It appears not all studies in the study collection have the same status on prolific. This shouldn't happen normally. If there is a timed out message at the top of the page, reload the page to see if all the api requests go through. Otherwise you can attempt to use the 'clear remote ids' on the study colleciton list page to reset the databses state to not track any prolific study ids. From there drafts will need to be created, published and participants added. Any current active or unpublished studies should be manually closed or deleted on prolific."

    studies_by_status.default_factory = None
    context = {
        "studies_by_status": studies_by_status,
        "study_collection": study_collection,
        "study_collection_subjects": study_collection_subjects,
        "id": id,
        "studies_in_db": studies_in_db,
        "publish": publish,
        "draft": draft,
        "add_parts": add_parts,
        "bad_state": bad_state,
        "state_description": state_description,
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
        print("in create view exception")
        print(e)
        print("!!!!!!!!!!!")
        messages.error(request, e)
    responses = json_encode_api_response(responses)
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

    responses = json_encode_api_response(responses)
    return render(
        request,
        "prolific/create_drafts_responses.html",
        {"responses": responses, "id": collection_id},
    )


def json_encode_api_response(responses):
    for response in responses:
        try:
            response = json.loads(response.content)
        except (json.JSONDecodeError, AttributeError):
            continue
    return responses


"""
    Summary and progress views
"""

""" Old production views. Test for removal
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
            battery__study__study_collection=collection_id, status='completed'
        ).annotate(prolific_id=F("subject__prolific_id"), parent=F("battery__title"))
    elif by == "result":
        recent = exp_models.Result.objects.filter(
            assignment__battery__study__study_collection=collection_id
        ).filter(status='completed').annotate(
            prolific_id=F("assignment__subject__prolific_id"),
            parent=F(
                "battery_experiment__experiment_instance__experiment_repo_id__name"
            ),
        )
    else:
        raise Http404("unsupported model")
    recent = recent.filter(status_changed__gte=td)
    return render(
        request,
        "prolific/collection_recently_completed.html",
        {"recent": recent, "td": td, "days": days, "collection": collection, "by": by},
    )


"""

"""
    collection_progress is the first stab at a progress page. Superceded by collection_progress_by_* views
"""


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
        if subjects.count() == 0 or not study.remote_id:
            break
        try:
            details = fetch_remote_study_details(id=study.remote_id)
        except Exception as e:
            errors.append(f"Error on {study.remote_id}: {e}")
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
    short-study object returned by list_submissions prolific endpoint
    Attributes:
        id (str): Submission id.
        participant_id (str): Participant id.
        status (SubmissionShortStatus): Status of the submission.
        started_at (datetime.datetime): Date started
        has_siblings (bool): Whether or not the submission has sibling submissions (sharing the same study).
        completed_at (Union[Unset, None, datetime.datetime]): Date completed
        study_code (Union[Unset, None, str]): The completion code used by the participant to complete the study.
"""


@login_required
def collection_progress_by_prolific_submissions(request, collection_id):
    context = {}

    collection = get_object_or_404(models.StudyCollection, id=collection_id)
    studies = collection.study_set.all().order_by("rank").prefetch_related("battery")
    collection_subjects = models.StudyCollectionSubject.objects.filter(
        study_collection=collection
    ).prefetch_related("subject")

    subject_study_status = {}
    for study in studies:
        api_results = outgoing_api.list_submissions(study.remote_id)
        for result in api_results:
            if not subject_study_status.get(result["participant_id"], None):
                subject_study_status[result["participant_id"]] = {}
            subject_study_status[result["participant_id"]][study.remote_id] = result[
                "status"
            ]

    no_api_result_subjects = [
        x.subject.prolific_id
        for x in collection_subjects
        if x.subject.prolific_id not in subject_study_status
    ]
    context = {
        "collection": collection,
        "studies": studies,
        "subject_study_status": subject_study_status,
        "no_api_result_subjects": no_api_result_subjects,
    }
    return render(
        request, "prolific/collection_progress_by_prolific_submissions.html", context
    )


@login_required
def collection_progress_by_experiment_submissions(request, collection_id):
    collection = get_object_or_404(models.StudyCollection, id=collection_id)
    studies = (
        collection.study_set.all()
        .order_by("rank")
        .prefetch_related("battery")
        .annotate(exp_count=Count("battery__experiment_instances"))
    )
    assignments = (
        exp_models.Assignment.objects.filter(
            subject__studycollectionsubject__study_collection=collection
        )
        .prefetch_related("battery")
        .annotate(result_count=Count("result"))
    )
    subjects = exp_models.Subject.objects.filter(
        studycollectionsubject__study_collection=collection
    )

    battery_assignments = defaultdict(lambda: defaultdict(list))
    for assignment in assignments:
        battery_assignments[assignment.battery_id][
            assignment.subject.prolific_id
        ].append(assignment.result_count)

    study_assignments = {}
    for study in studies:
        batt_assignments = battery_assignments[study.battery.id]
        single_assignment_per_subject = {
            sub: assignment.pop()
            for sub, assignment in batt_assignments.items()
            if len(assignment)
        }
        study_assignments[study.id] = (study, single_assignment_per_subject)

    context = {
        "collection": collection,
        "studies": studies,
        "assignments": assignments,
        "subjects": [x.prolific_id for x in subjects],
        "study_assignments": study_assignments,
    }
    return render(
        request, "prolific/collection_progress_by_experiment_submissions.html", context
    )


@login_required
def collection_recently_completed(request, collection_id, days, by):
    collection = get_object_or_404(models.StudyCollection, id=collection_id)
    td = timezone.now() - timedelta(days=days)
    if by == "assignment":
        recent = (
            exp_models.Assignment.objects.filter(
                battery__study__study_collection=collection_id
            )
            .filter(status="completed")
            .annotate(
                subject_id="subject__id",
                prolific_id=F("subject__prolific_id"),
                parent=F("battery__title"),
            )
        )
    elif by == "result":
        recent = (
            exp_models.Result.objects.filter(
                assignment__battery__study__study_collection=collection_id
            )
            .filter(status="completed")
            .annotate(
                prolific_id=F("assignment__subject__prolific_id"),
                parent=F(
                    "battery_experiment__experiment_instance__experiment_repo_id__name"
                ),
            )
        )
    else:
        raise Http404("unsupported model")
    recent = recent.filter(status_changed__gte=td)
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
    limit = int(request.GET.get("limit", -1))
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
    subjects = subjects.distinct()
    if limit:
        subjects = subjects[:limit]
    context["subjects"] = subjects
    return render(request, "prolific/recent_participants.html", context)


"""
    Summary and progress views end
"""

"""
    Should probably exist as a method of the form itself.
    given a list of prolific Ids and study collection:
        - create Subject instances for PIDs if they don't exist.
        - StudyCollectionSubject, permenatly links collection and pid.
        - Create a StudySubject and by association for first study.
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
            subject, sub_created = exp_models.Subject.objects.get_or_create(
                prolific_id=id
            )
            subjects.append(subject)

        first_study = collection.study_set.first()
        for subject in subjects:
            (
                subject_collection,
                created,
            ) = models.StudyCollectionSubject.objects.get_or_create(
                study_collection=collection, subject=subject
            )
            if first_study:
                study_subject, created = models.StudySubject.objects.get_or_create(
                    study=first_study, subject=subject
                )
            print(f"first study: {first_study}, ss.study: {study_subject.study}")
            if created:
                on_add_to_collection(subject_collection)
            if first_study and created:
                subject_collection.current_study = first_study

        if first_study:
            print(f"calling add to allow on {first_study.id} with pids: {ids}")
            first_study.add_to_allowlist(ids)
        """
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
        """

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


"""
    View that displays all the subjects that have been associated with a study colleciton.
    This is typically done when a prolific ID is added to the first study in a study collection.
"""


@login_required
def study_collection_subject_list(request, collection_id):
    collection = get_object_or_404(models.StudyCollection, pk=collection_id)
    study_collection_subjects = models.StudyCollectionSubject.objects.filter(
        study_collection__pk=collection_id
    ).select_related("subject")
    context = {
        "study_collection_subjects": study_collection_subjects,
        "collection": collection,
    }
    return render(request, "prolific/study_collection_subjects.html", context)


@login_required
def reissue_incomplete_study_collection(request, scs_id):
    scs = get_object_or_404(models.StudyCollectionSubject, pk=scs_id)
    responses, new_scs = scs.incomplete_study_collection()
    context = {"responses": responses, "old_scs": scs, "new_scs": new_scs}
    return render(request, "prolific/reissue_incomplete_study_collection.html", context)


@login_required
def study_collection_subject_detail(
    request, scs_id=None, collection_id=None, prolific_id=None
):
    if scs_id:
        scs = get_object_or_404(models.StudyCollectionSubject, pk=scs_id)
    else:
        scs = get_object_or_404(
            models.StudyCollectionSubject,
            study_collection__id=collection_id,
            subject__prolific_id=prolific_id,
        )
    status = []
    study_subjects = models.StudySubject.objects.filter(subject=scs.subject, study__study_collection=scs.study_collection).order_by('study__rank')
    for ss in study_subjects:
        if not ss.prolific_session_id:
            prolific_status = "No Session ID"
        else:
            prolific_status = x.get_prolific_status()
        status.append((ss, prolific_status))
    context = {
        "scs": scs,
        "status": status,
    }

    return render(request, "prolific/study_collection_subject_detail.html", context)


@login_required
def study_subject_by_collection(request, collection_id):
    study_subjects = models.StudySubject.objects.get(
        collection__id=collection_id
    ).select_related()
    context = {"study_subjects": study_subjects}
    return render(request, "prolific/study_subjects_by_collection.html", context)


@login_required
def delete_study_subject_relations(request, collection_id, subject_id):
    stSubs = models.StudySubject.objects.filter(
        study__study_collection__id=collection_id, subject__prolific_id=subject_id
    )
    print(stSubs)
    if stSubs:
        [x.assignment.delete() for x in stSubs]
    scs = models.StudyCollectionSubject.objects.filter(
        study_collection__id=collection_id, subject__prolific_id=subject_id
    )
    print(scs)
    [x.delete() for x in scs]
    return HttpResponseRedirect(
        reverse_lazy(
            "prolific:collection-subject-list", kwargs={"collection_id": collection_id}
        )
    )


@login_required
def toggle_active_study_collection_subject(request, scs_id):
    scs = get_object_or_404(models.StudyCollectionSubject, id=scs_id)
    scs.active = not scs.active
    return redirect(reverse('prolific:collection-subject-detail', kwargs={'scs_id': scs.id}))

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


