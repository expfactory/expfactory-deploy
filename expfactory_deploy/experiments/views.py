import json
import sys
from datetime import datetime
from pathlib import Path

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.db.models import F, Q
from django.forms import formset_factory, TextInput
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from taggit.models import Tag

from experiments import forms as forms
from experiments import models as models
from experiments.utils.repo import find_new_experiments, get_latest_commit

sys.path.append(Path(settings.ROOT_DIR, "expfactory_deploy_local"))

from expfactory_deploy_local.utils import generate_experiment_context

# Repo Views

class RepoOriginList(ListView):
    model = models.RepoOrigin
    queryset = models.RepoOrigin.objects.prefetch_related("experimentrepo_set")

class RepoOriginCreate(CreateView):
    model = models.RepoOrigin
    form_class = forms.RepoOriginForm
    success_url = reverse_lazy("experiments:experiment-repo-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.clone()
        return response

# Experiment Views
def experiment_instances_from_latest(experiment_repos):
    for experiment_repo in experiment_repos:
        latest = get_latest_commit(experiment_repo.location)
        ExperimentInstance.get_or_create(
            experiment_repo_id=experiment_repo.id, commit=latest
        )


class ExperimentRepoList(ListView):
    model = models.ExperimentRepo
    queryset = models.ExperimentRepo.objects.prefetch_related("origin", "tags").filter(origin__active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = [x['name'] for x in Tag.objects.all().values('name')]
        tags.append('')
        context['tags'] = tags
        context['tag_form'] = forms.ExperimentRepoBulkTagForm()
        return context

class ExperimentRepoDetail(DetailView):
    model = models.ExperimentRepo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batteries = models.Battery.objects.filter(batteryexperiments__experiment_instance__experiment_repo_id=self.get_object())
        results = models.Result.objects.filter(battery_experiment__experiment_instance__experiment_repo_id=self.get_object())
        batt_results = [(batt, list(results.filter(battery_experiment__battery=batt))) for batt in batteries]
        context['batt_results'] = batt_results
        return context


def add_new_experiments(request):
    created_repos, created_experiments, errors = find_new_experiments()
    for repo in created_repos:
        messages.info(request, f"Tracking previously unseen repository {repo.url}")
    for experiment in created_experiments:
        messages.info(request, f"Added new experiment {experiment.name}")
    for error in errors:
        messages.error(request, error)
    return redirect('/experiments')

def repo_instances(request, pk):
    instances = models.ExperimentInstances.objects.filter(experiment_repo_id=pk).all()
    render(request, "experiments/experimentinstances_select.html", {instances: instances})

class ExperimentRepoUpdate(UpdateView):
    model = models.ExperimentRepo
    form_class = forms.ExperimentRepoForm
    success_url = reverse_lazy("experiments:experiment-repo-list")

class ExperimentRepoDelete(DeleteView):
    model = models.ExperimentRepo
    success_url = reverse_lazy("experiments:experiment-repo-list")

class ExperimentInstanceCreate(CreateView):
    model = models.ExperimentInstance
    form_class = forms.ExperimentInstanceForm
    success_url = reverse_lazy("experiments:experiment-instance-detail")

class ExperimentInstanceUpdate(UpdateView):
    model = models.ExperimentInstance
    form_class = forms.ExperimentInstanceForm
    success_url = reverse_lazy("experiments:experiment-instance-detail")

class ExperimentInstanceDetail(DetailView):
    model = models.ExperimentInstance


# Battery Views

# Inject list of experiment repos into a context and the id attribute used by the form
def add_experiment_repos(context, battery=None):
    if battery:
        qs = models.ExperimentRepo.objects.filter(
            Q(origin__active=True) | Q(experimentinstance__battery__id=battery.id)
        ).distinct().all().prefetch_related("origin")
    else:
        qs = models.ExperimentRepo.objects.filter(origin__active=True).all().prefetch_related("origin")
    context[
        "experiment_repo_list"
    ] = qs
    context["exp_repo_select_id"] = "place_holder"


class BatteryList(ListView):
    model = models.Battery

    def get_queryset(self):
        return models.Battery.objects.filter(status='template').prefetch_related("children")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        statuses = [x[0] for x in self.model.STATUS]
        context['statuses'] = statuses
        return context


class BatteryDetail(DetailView):
    model = models.Battery
    queryset = models.Battery.objects.prefetch_related("assignment_set", "experiment_instances")
    context_object_name = "battery"


"""
    View used for battery creation. Handles creating expdeirmentinstance
    objects and order entries in the battery <-> experiment instance pivot table
    as needed.
"""
class BatteryComplex(TemplateView):
    template_name = "experiments/battery_form.html"
    battery = None
    battery_kwargs = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = models.ExperimentInstance.objects.none()
        ordering = None
        if self.battery:
            qs = self.battery.experiment_instances.all()
            ordering = qs.annotate(exp_order=F('batteryexperiments__order'))
            context['battery'] = self.battery
        context["form"] = forms.BatteryForm(**self.battery_kwargs)

        add_experiment_repos(context, self.battery)
        context["exp_instance_formset"] = forms.ExpInstanceFormset(
            queryset=qs, form_kwargs={"ordering": ordering}
        )
        context["test_exp_instance_formset"] = forms.TestExpInstanceFormset(
            queryset=qs
        )
        context["battery_experiments_formset"] = forms.BatteryExperimentsFormset(
            queryset=self.battery.batteryexperiments_set.all()
        )
        return context

    def get_object(self):
        battery_id = self.kwargs.get("pk")
        if battery_id is not None:
            battery = get_object_or_404(models.Battery, pk=battery_id)
            self.battery = battery
            self.battery_kwargs = {"instance": battery}

    def get(self, request, *args, **kwargs):
        self.get_object()
        if self.battery and self.battery.status in ['published', 'inactive']:
            return redirect("experiments:battery-detail", pk=self.battery.id)
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.get_object()
        form = forms.BatteryForm(self.request.POST, **self.battery_kwargs)
        form.instance.user = request.user
        battery = form.save()

        ordering = models.ExperimentInstance.objects.filter(
            batteryexperiments__battery=self.battery
        ).order_by("batteryexperiments__order")
        exp_instance_formset = forms.ExpInstanceFormset(
            self.request.POST, form_kwargs={"battery_id": battery.id}
        )
        valid = exp_instance_formset.is_valid()
        if valid:
            ei = exp_instance_formset.save()
            battery.batteryexperiments_set.exclude(experiment_instance__in=ei).delete()
        elif not valid:
            print(exp_instance_formset.errors)
        if form.is_valid():
            return HttpResponseRedirect("/battery/")
        else:
            print(form.errors)
            return HttpResponseRedirect(reverse_lazy("battery-list"))

@login_required
def publish_battery(request, pk):
    battery = get_object_or_404(models.Battery, pk=pk)
    battery.status = "published"
    battery.save()
    return HttpResponseRedirect(reverse_lazy("experiments:battery-detail", {pk:pk}))

@login_required
def publish_battery_confirmation(request, pk):
    battery = get_object_or_404(models.Battery, pk=pk)
    return render(request, 'experiments/battery_publish_confirmation.html', {'battery': battery})

@login_required
def deactivate_battery(request, pk):
    battery = get_object_or_404(models.Battery, pk=pk)
    battery.status = "inactive"
    battery.save()
    return HttpResponseRedirect(reverse_lazy("experiments:battery-list"))

@login_required
def deactivate_battery_confirmation(request, pk):
    battery = get_object_or_404(models.Battery, pk=pk)
    return render(request, 'experiments/battery_deactivate_confirmation.html', {'battery': battery})

@login_required
def deactivate_repo(request, pk):
    repo = get_object_or_404(models.RepoOrigin, pk=pk)
    repo.active = False
    repo.save()
    return HttpResponseRedirect(reverse_lazy("experiments:experiment-repo-list"))

@login_required
def deactivate_repo_confirmation(request, pk):
    repo = get_object_or_404(models.RepoOrigin, pk=pk)
    print(repo.url)
    return render(request, 'experiments/repo_deactivate_confirmation.html', {'repo': repo})

class BatteryClone(View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        batt = get_object_or_404(models.Battery, pk=pk)
        return redirect('experiments:battery-list')

"""
class BatteryDeploymentDelete(DeleteView):
    model = models.Battery
    success_url = reverse_lazy('battery-list')
"""

def jspsych_context(exp_instance):
    deploy_static_fs = exp_instance.deploy_static()
    deploy_static_url = deploy_static_fs.replace(
        settings.DEPLOYMENT_DIR, settings.STATIC_DEPLOYMENT_URL
    )
    location = exp_instance.experiment_repo_id.location
    exp_fs_path = Path(deploy_static_fs, Path(location).stem)
    exp_url_path = Path(deploy_static_url, Path(location).stem)

    # default js/css location for poldracklab style experiments
    static_url_path = Path(settings.STATIC_NON_REPO_URL, "default")

    return generate_experiment_context(
        exp_fs_path, static_url_path, exp_url_path
    )

class Preview(View):
    def get(self, request, *args, **kwargs):
        exp_id = self.kwargs.get("exp_id")
        experiment = get_object_or_404(models.ExperimentRepo, id=exp_id)
        commit = experiment.get_latest_commit()
        exp_instance, created = models.ExperimentInstance.objects.get_or_create(
            experiment_repo_id=experiment, commit=commit
        )

        # Could embed commit or instance id in kwargs, default to latest for now
        # default template for poldracklab style experiments
        template = "experiments/jspsych_deploy.html"
        context = jspsych_context(exp_instance)
        return render(request, template, context)

class PreviewBattery(View):
    def get(self, request, *args, **kwargs):
        battery_id = self.kwargs.get("battery_id")
        battery = get_object_or_404(models.Battery, id=battery_id)
        # make preview subject
        date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        handle = f"preview_{battery_id}_{date}"
        preview_sub = models.Subject(handle=handle)
        preview_sub.save()
        assignment = models.Assignment(subject=preview_sub, battery=battery)
        assignment.save()
        return redirect('experiments:serve-battery', subject_id=preview_sub.id, battery_id=battery_id)

class Serve(TemplateView):
    subject = None
    battery = None
    experiment = None
    assignment = None

    def get_template_names(self):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response() is overridden.
        """
        return ["experiments/jspsych_deploy.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def set_objects(self):
        subject_id = self.kwargs.get("subject_id")
        battery_id = self.kwargs.get("battery_id")
        """ we might accept the uuid assocaited with the subject instead of its id """
        if subject_id is not None:
            self.subject = get_object_or_404(
                models.Subject, id=subject_id
            )
        else:
            self.subject = None
        self.battery = get_object_or_404(
            models.Battery, id=battery_id
        )
        try:
            self.assignment = models.Assignment.objects.get(
                subject=self.subject, battery=self.battery
            )
        except ObjectDoesNotExist:
            # make new assignment for testing, in future 404.
            assignment = models.Assignment(
                subject_id=subject_id, battery_id=battery_id,
            )
            assignment.save()
            self.assignment = assignment

    def get(self, request, *args, **kwargs):
        self.set_objects()
        if self.assignment.consent_accepted is not True:
            # display instructions and consent
            pass

        self.experiment = self.assignment.get_next_experiment()

        if self.experiment is None:
            return redirect('experiments:battery-list')

        exp_context = jspsych_context(self.experiment)
        exp_context["post_url"] = reverse_lazy("experiments:push-results", args=[self.assignment.id, self.experiment.id])
        exp_context["next_page"] = reverse_lazy("serve-battery", args=[self.subject.id, self.battery.id])
        context = {**self.get_context_data(), **exp_context}
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return

class Results(View):
    # If more frameworks are added this would dispatch to their respective
    # versions of this function.
    # expfactory-docker purges keys and process survey data at this step
    def process_exp_data(self, post_data, assignment):
        data = json.loads(post_data)
        finished = data.get("status") == "finished"
        if assignment.status == "not-started":
            assignment.status = "started"
        return data, finished

    def post(self, request, *args, **kwargs):
        assignment_id = self.kwargs.get("assignment_id")
        experiment_id = self.kwargs.get("experiment_id")
        exp_instance = get_object_or_404(models.ExperimentInstance, id=experiment_id)
        assignment = get_object_or_404(models.Assignment, id=assignment_id)
        batt_exp = get_object_or_404(models.BatteryExperiments, battery=assignment.battery, experiment_instance=exp_instance)
        data, finished = self.process_exp_data(request.body, assignment)
        if finished:
            models.Result(assignment=assignment, battery_experiment=batt_exp, subject=assignment.subject, data=data, status="completed").save()
        elif assignment.status == "not-started":
            assignment.status = "started"
        assignment.save()
        return HttpResponse('recieved')

class SubjectDetail(DetailView):
    model = models.Subject

class SubjectList(ListView):
    model = models.Subject
    queryset = models.Subject.objects.filter(active=True).prefetch_related("assignment_set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject_select'] = forms.SubjectActionForm()
        return context

class CreateSubjects(FormView):
    template_name = 'experiments/create_subjects.html'
    form_class = forms.SubjectCount
    success_url = reverse_lazy('experiments:subject-list')
    def form_valid(self, form):
        new_subjects = [models.Subject() for i in range(form.cleaned_data['count'])]
        models.Subject.objects.bulk_create(new_subjects)
        return super().form_valid(form)

class SubjectListAction(FormView):
    template_name = 'experiments/subject_list.html'
    form_class = forms.SubjectActionForm
    success_url = reverse_lazy('experiments:subject-list')

class ToggleSubjectActivation(SubjectListAction):
    def form_valid(self, form):
        models.Subject.objects.filter(id__in=form.cleaned_data['subjects']).update(active=Q(active=False))
        return super().form_valid(form)

class AssignSubject(SubjectListAction):
    def form_valid(self, form):
        subs = models.Subject.objects.filter(id__in=form.cleaned_data['subjects'])
        batts = models.Battery.objects.filter(id__in=form.cleaned_data['batteries'])
        assignments = []
        for batt in batts:
            for sub in subs:
                try:
                    models.Assignment.objects.get(subject=sub, battery=batt)
                except ObjectDoesNotExist:
                    assignments.append(models.Assignment(subject=sub, battery=batt))

        models.Assignment.objects.bulk_create(assignments)

        return super().form_valid(form)

class ExperimentRepoBulkTag(FormView):
    form_class = forms.ExperimentRepoBulkTagForm
    template_name = 'experiments/experimentrepo_list.html'
    success_url = reverse_lazy('experiments:experiment-repo-list')
    def form_valid(self, form):
        exp_repos = models.ExperimentRepo.objects.filter(id__in=form.cleaned_data['experiments'])
        print(form.cleaned_data['experiments'])
        print(form.cleaned_data['tags'])
        action = self.kwargs.get('action')
        for exp_repo in exp_repos:
            if action == 'add':
                exp_repo.tags.add(*form.cleaned_data['tags'])
            elif action == 'remove':
                exp_repo.tags.remove(*form.cleaned_data['tags'])
            exp_repo.save()
        return super().form_valid(form)

