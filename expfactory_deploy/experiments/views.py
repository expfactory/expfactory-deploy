import sys
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from experiments import forms as forms
from experiments import models as models
from experiments.utils.repo import find_new_experiments, get_latest_commit

sys.path.append(Path(settings.ROOT_DIR, "expfactory_deploy_local"))

from expfactory_deploy_local.utils import generate_experiment_context


# Experiment Views
def experiment_instances_from_latest(experiment_repos):
    for experiment_repo in experiment_repos:
        latest = get_latest_commit(experiment_repo.location)
        ExperimentInstance.get_or_create(
            experiment_repo_id=experiment_repo.id, commit=latest
        )


class ExperimentRepoList(ListView):
    model = models.ExperimentRepo
    queryset = models.ExperimentRepo.objects.prefetch_related("origin")


class ExperimentRepoDetail(DetailView):
    model = models.ExperimentRepo


def add_new_experiments(request):
    created_repos, created_experiments, errors = find_new_experiments()
    for repo in created_repos:
        messages.info(request, f"Tracking previously unseen repository {repo.origin}")
    for experiment in created_experiments:
        messages.info(request, f"Added new experiment {experiment.name}")
    for error in errors:
        messages.error(request, error)
    return redirect('/experiments')


class ExperimentRepoUpdate(UpdateView):
    model = models.ExperimentRepo
    fields = ["name"]


class ExperimentRepoDelete(DeleteView):
    model = models.ExperimentRepo
    success_url = reverse_lazy("experiment-repo-list")


# Battery Views

# Inject list of experiment repos into a context and the id attribute used by the form
def add_experiment_repos(context):
    context[
        "experiment_repo_list"
    ] = models.ExperimentRepo.objects.all().prefetch_related("origin")
    context["exp_repo_select_id"] = "place_holder"


class BatteryList(ListView):
    model = models.Battery

    def get_queryset(self):
        return models.Battery.objects.filter(status='template').prefetch_related("children")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class BatteryDetail(DetailView):
    model = models.Battery
    queryset = models.Battery.objects.prefetch_related('experiment_instances')


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
            qs = models.ExperimentInstance.objects.filter(
                batteryexperiments__battery=self.battery
            ).order_by("batteryexperiments__order")
            ordering = qs.annotate(exp_order=F("batteryexperiments__order"))
        context["form"] = forms.BatteryForm(**self.battery_kwargs)

        add_experiment_repos(context)
        context["exp_instance_formset"] = forms.ExpInstanceFormset(
            queryset=qs, form_kwargs={"ordering": ordering}
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
        if self.battery.status in ['published', 'inactive']:
            return redirect("experiments:battery-detail", pk=self.battery.id) 
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.get_object()
        form = forms.BatteryForm(self.request.POST, **self.battery_kwargs)
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


class Preview(View):
    def get(self, request, *args, **kwargs):
        exp_id = self.kwargs.get("exp_id")
        experiment = get_object_or_404(models.ExperimentRepo, id=exp_id)
        # Could embed commit or instance id in kwargs, default to latest for now
        commit = experiment.get_latest_commit()
        exp_instance, created = models.ExperimentInstance.objects.get_or_create(
            experiment_repo_id=experiment, commit=commit
        )
        deploy_static_fs = exp_instance.deploy_static()
        deploy_static_url = deploy_static_fs.replace(
            settings.DEPLOYMENT_DIR, settings.STATIC_DEPLOYMENT_URL
        )
        exp_fs_path = Path(deploy_static_fs, Path(experiment.location).stem)
        exp_url_path = Path(deploy_static_url, Path(experiment.location).stem)

        # default template for poldracklab style experiments
        template = "experiments/jspsych_deploy.html"
        # default js/css location for poldracklab style experiments
        static_url_path = Path(settings.STATIC_NON_REPO_URL, "default")

        context = generate_experiment_context(
            exp_fs_path, static_url_path, exp_url_path
        )
        return render(request, template, context)


class Serve(TemplateView):
    worker = None
    battery = None
    experiment = None
    assignment = None

    def get_template_names(self):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response() is overridden.
        """
        return ["experiments/____.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def set_objects(self):
        subject_id = self.kwargs.get("subject_id")
        battery_id = self.kwargs.get("battery_id")
        """ we might accept the uuid assocaited with the worker instead of its id """
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
            self.assignment = models.Assignment.get(
                subject=self.subject, battery=self.battery
            )
        except ObjectDoesNotExist:
            # make new one?
            pass

    def get(self, request, *args, **kwargs):
        self.set_objects()
        if self.assignment.consent_accepted is not True:
            # display instructions and consent
            pass

        self.assignment.get_next_experiment()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        return

class SubjectList(ListView):
    model = models.Subject

class CreateSubjects(FormView):
    template_name = 'experiments/create_subjects.html'
    form_class = forms.SubjectCount
    success_url = reverse_lazy('experiments:subject-list')
    def form_valid(self, form):
        new_subjects = [models.Subject() for i in range(form.cleaned_data['count'])]
        models.Subject.objects.bulk_create(new_subjects)
        return super().form_valid(form)
