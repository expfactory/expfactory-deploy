import json
import pprint

from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, FormView, UpdateView

from experiments import views as exp_views
from experiments import models as exp_models

from prolific import models
from prolific import forms
from prolific import outgoing_api

class ProlificServe(exp_views.Serve):
    def set_subject(self):
        prolific_id = self.request.GET.get('PROLIFIC_PID', None)
        if prolific_id is None:
            self.subject = None
        else:
            self.subject = exp_models.Subject.objects.get_or_create(prolific_id=prolific_id)[0]

    def complete(self, request):
        return redirect(reverse('prolific:complete', kwargs={'assignment_id': self.assignment.id}))

class ProlificComplete(View):
    def get(self, request, *args, **kwargs):
        assignment = get_object_or_404(
            models.Assignment,
            id=self.kwargs.get('assignment_id')
        )
        cc_url = None
        try:
            cc = models.SimpleCC.objects.get(battery=assignment.battery)
            cc_url = cc.completion_url
        except ObjectDoesNotExist:
            pass

        return render(request, "prolific/complete.html", {'completion_url': cc_url})

class SimpleCCUpdate(UpdateView):
    form_class = forms.SimpleCCForm
    template_name = 'prolific/simplecc_form.html'

    def get_success_url(self):
        pk = self.kwargs.get('battery_id')
        return reverse('experiments:battery-detail', kwargs={'pk': pk})

    def get_object(self, queryset=None):
        return models.SimpleCC.objects.get_or_create(battery_id=self.kwargs.get('battery_id'), defaults={'completion_url': ''})[0]

class StudyCollectionList(ListView):
    model = models.StudyCollection

class StudyCollectionView(LoginRequiredMixin, TemplateView):
    template_name = "prolific/study_collection.html"
    collection = None
    collection_kwargs = {}

    def get_object(self):
        collection_id = self.kwargs.get("collection_id")
        if collection_id is not None:
            self.collection = get_object_or_404(models.StudyCollection, pk=collection_id)
            self.collection_kwargs={'instance': self.collection}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "form" not in kwargs:
            context["form"] = forms.StudyCollectionForm(**self.collection_kwargs)
        else:
            context["form"] = kwargs.get("form")

        initial = []
        if self.collection:
            initial = list(
                models.Study.objects.filter(study_collection=self.collection)
                    .values('battery', 'rank')
            )
        if "study_rank_formset" not in kwargs:
            context["study_rank_formset"] = forms.BatteryRankFormset(initial=initial)
        else:
            context["study_rank_formset"] = kwargs.get("studyrankformset")

        context['batteries'] = exp_models.Battery.objects.exclude(status__in=['template', 'inactive']).values_list('id', 'title')

        return context

    def get(self, request, *args, **kwargs):
        self.get_object()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.get_object()
        form = forms.StudyCollectionForm(self.request.POST, **self.collection_kwargs)
        form.instance.user = request.user
        collection = form.save()

        print(self.request.POST)
        study_rank_formset = forms.BatteryRankFormset(
            self.request.POST
        )

        if study_rank_formset.is_valid():
            study_set = list(self.collection.study_set.all())
            for i, form in enumerate(study_rank_formset):
                print(form.cleaned_data)
                print(dir(form.cleaned_data))
                batt = form.cleaned_data['battery']
                rank = form.cleaned_data['rank']
                if i < len(study_set):
                    study_set[i].battery = batt
                    study_set[i].rank = rank
                    study_set[i].save()
                else:
                    new_study = models.Study(battery=batt, rank=rank, study_collection=self.collection)
                    new_study.save()
            [x.delete() for x in study_set[len(study_rank_formset):]]
        else:
            print(study_rank_formset.errors)
            return self.render_to_response(self.get_context_data(form=form, study_rank_formset=study_rank_formset))

        if form.is_valid():
            return HttpResponseRedirect(reverse_lazy("prolific:study-collection-list"))
        else:
            print(form.errors)
            return HttpResponseRedirect(reverse_lazy("prolific:study-collection-update"))

@login_required
def remote_studies_list(request):
    studies = outgoing_api.list_studies()
    return render(request, "prolific/remote_studies_list.html", {"studies": studies})

@login_required
def remote_study_detail(request, id=None):
    study = outgoing_api.study_detail(id)
    jsn = json.dumps(study)
    return render(request, "prolific/remote_study_detail.html", {"study": study, "json": jsn})


class ParticipantFormView(LoginRequiredMixin, FormView):
    template_name = "prolific/participant_form.html"
    form_class = forms.ParticipantIdForm
    success_url = reverse_lazy('prolific:study-collection-list')

    '''
    Should probably exist as a method of the form itself.
    given a list of prolific Ids and study collection:
        - create Subject instances for PIDs if they don't exist.
        - create assignments if subject was created?
        - StudyCollectionSubject, permenatly links collection and pid.
            - What are we really doing with this model?
        - See what batteries subject has completed
            - find earliest incomplete in StudyCollection rank order.
            - via prolific api add them to partgroup/allowlist/etc...

    '''
    def form_valid(self, form):
        ids = form.cleaned_data['ids']
        collection = get_object_or_404(models.StudyCollection, id=self.kwargs['collection_id'])

        subjects = []
        for id in ids:
            subject, created = exp_models.Subject.objects.get_or_create(prolific_id=id)
            subjects.append(subject)

        for subject in subjects:
            subject_collection, created = models.StudyCollectionSubject.objects.get_or_create(study_collection=collection, subject=subject)

        pids_to_add = defaultdict(list)
        studies = models.Study.objects.filter(study_collection=collection).order_by('rank')
        # Only works with study in inner for loop, we only want to add each subject at most once to an allowlist in this call.
        for subject in subjects:
            for study in studies:
                completed = exp_models.Assignment.objects.filter(status="completed", subject=subject, battery=study.battery)
                if len(completed) == 0:
                    pids_to_add[study.remote_id].append(subject.prolific_id)
                    break

        for study in studies:
            study.add_to_allowlist(pids_to_add[study.remote_id])

        return super().form_valid(form)
