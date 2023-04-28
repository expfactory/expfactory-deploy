import re

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.urls.exceptions import NoReverseMatch
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.views.generic import TemplateView

from mturk import forms as forms
from mturk import boto_utils
from mturk import models as models
from experiments.models import Battery, Subject


def battery_id_from_url(url):
    pattern = "/serve/(\d+)/"
    match = re.search(pattern, url)
    if match is None:
        return None
    try:
        return match.group(1)
    except IndexError:
        return None


class HitGroupCreateUpdate(LoginRequiredMixin, TemplateView):
    template_name = "mturk/hitgroup_form.html"
    hit_group = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        battery = None
        if self.hit_group is None:
            battery_id = kwargs.get("battery_id", None)
            try:
                battery = Battery.objects.get(pk=battery_id)
            except Battery.DoesNotExist:
                battery = None

        context["hit_group_form"] = forms.HitGroupForm(
            self.hit_group, initial={"battery": battery}
        )
        details = None
        if self.hit_group is not None:
            details = self.hit_group.get("details", None)
        context["hit_group_details_form"] = forms.HitGroupDetailsForm(instance=details)
        return context

    def get_object(self):
        hit_group_id = self.kwargs.get("pk", None)
        if hit_group_id is not None:
            self.hit_group = get_object_or_404(models.HitGroup, pk=hit_group_id)

    def get(self, request, *args, **kwargs):
        self.get_object()
        if not self.hit_group or self.hit_group.get("published", None) is None:
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
        else:
            redirect("mturk:hitgroup-detail", pk=self.hit_group.pk)

    def post(self, request, *args, **kwargs):
        self.get_object()
        hit_group_form = forms.HitGroupForm(request.POST, instance=self.hit_group)
        hit_group_details_form = forms.HitGroupDetailsForm(
            request.POST, instance=self.hit_group.get("details", None)
        )

        if hit_group_form.is_valid() and hit_group_details_form.is_valid():
            hit_group_form.save()
            hit_group_details_form.save()
            # Actually make mturk calls
            # I mean should really go in models
            return redirect("mturk:hitgroup-detail", pk=self.hit_group.pk)
        else:
            context = self.get_context_data(**kwargs)
            context["hit_group_form"] = hit_group_form
            context["hit_group_details_form"] = hit_group_details_form
            return self.render_to_response(context)


@login_required
def hits_list(request, url=None):
    client = boto_utils.BotoWrapper()
    hits_by_url = client.get_hits(url)
    battery_urls = {}
    for key in hits_by_url.keys():
        bid = battery_id_from_url(key)
        try:
            detail_url = reverse("experiments:battery-detail", args=[bid])
        except NoReverseMatch:
            detail_url = None
        battery_urls[key] = detail_url
    all = False if url else True
    context = {
        "hits_by_url": dict(hits_by_url),
        "battery_urls": battery_urls,
        "all": all,
    }
    return render(request, "mturk/list_hits.html", context)


@login_required
def summaries_list(request):
    client = boto_utils.BotoWrapper()
    hits = client.get_hits()
    summaries = []
    for key in hits.keys():
        bid = battery_id_from_url(key)
        try:
            detail_url = reverse("experiments:battery-detail", args=[bid])
        except NoReverseMatch:
            detail_url = None
        summary = {
            "url": key,
            "detail_url": detail_url,
            "pending": 0,
            "available": 0,
            "complete": 0,
            "total": 0,
            "earliest_expiration": None,
            "completed": 0,
            "total_hits": len(hits[key]),
        }
        for hit in hits[key]:
            summary["available"] += hit["NumberOfAssignmentsAvailable"]
            summary["complete"] += hit["NumberOfAssignmentsCompleted"]
            summary["pending"] += hit["NumberOfAssignmentsPending"]
            summary["total"] += hit["MaxAssignments"]
            if (
                summary["earliest_expiration"] is None
                or hit["Expiration"] < summary["earliest_expiration"]
            ):
                summary["earliest_expiration"] = hit["Expiration"]
        summaries.append(summary)

    context = {"summaries": summaries}
    return render(request, "mturk/summaries.html", context)


@login_required
def assignments_list(request, url):
    client = boto_utils.BotoWrapper()
    assignments = client.list_assignments(url)
    bid = battery_id_from_url(url)
    context = {assignments: assignments, bid: bid}
    return render(request, "mturk/assignments_list.html", context)


# should we delete the hit?
@login_required
def expire_hit(request, hit_id):
    client = boto_utils.BotoWrapper()
    client.expire_hits_by_id([hit_id])
    client.delete_hits_by_id([hit_id])
    return redirect("mturk:hits-list")
