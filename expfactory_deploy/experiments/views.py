from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from experiments import forms as forms
from experiments import models as models
from experiments.utils.repo import find_new_experiments, get_latest_commit

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
    created_repos, created_experiments = find_new_experiments()
    for repo in created_repos:
        messages.info(request, f"Tracking previously unseen repository {repo.origin}")
    for experiment in created_experiemtns:
        messages.info(request, f"Added new experiment {experiment.name}")
    return reverse_lazy("experiment-repo-list")


class ExperimentRepoUpdate(UpdateView):
    model = models.ExperimentRepo
    fields = ["name"]


class ExperimentRepoDelete(DeleteView):
    model = models.ExperimentRepo
    success_url = reverse_lazy("expeirment-repo-list")


# Battery Views

# Inject list of experiment repos into a context and the id attribute used by the form
def add_experiment_repos(context):
    context[
        "experiment_repo_list"
    ] = models.ExperimentRepo.objects.all().prefetch_related("origin")
    context["exp_repo_select_id"] = "place_holder"


class BatteryList(ListView):
    model = models.Battery


class BatteryDetail(DetailView):
    model = models.Battery


class BatteryComplex(TemplateView):
    template_name = "experiments/battery_form.html"
    battery = None
    battery_kwargs = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ordering = models.ExperimentInstance.objects.none()
        initial = None
        if self.battery:
            ordering = models.ExperimentInstance.objects.filter(
                batteryexperiments__battery=self.battery
            ).order_by("batteryexperiments__order")
        context["form"] = forms.BatteryForm(**self.battery_kwargs)

        add_experiment_repos(context)
        context["exp_instance_formset"] = forms.ExpInstanceFormset(queryset=ordering)
        return context

    def get_object(self):
        battery_id = self.kwargs.get("pk")
        if battery_id is not None:
            battery = get_object_or_404(models.Battery, pk=battery_id)
            self.battery = battery
            self.battery_kwargs = {"instance": battery}

    def get(self, request, *args, **kwargs):
        self.get_object()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.get_object()
        form = forms.BatteryForm(self.request.POST, **self.battery_kwargs)
        battery = form.save()

        ordering = models.ExperimentInstance.objects.filter(
            batteryexperiments__battery=self.battery
        ).order_by("batteryexperiments__order")

        exp_instance_formset = forms.ExpInstanceFormset(
            self.request.POST, queryset=ordering
        )

        valid = exp_instance_formset.is_valid()
        if valid:
            for order, form in enumerate(exp_instance_formset.ordered_forms):
                print(form.cleaned_data)
                exp_inst = form.save()
                models.BatteryExperiments.objects.get_or_create(
                    battery=battery, experiment_instance=exp_inst, order=order
                )
        else:
            print(exp_instance_formset.errors)
        if form.is_valid():
            return HttpResponseRedirect("/battery/")
        else:
            return HttpResponseRedirect(reverse_lazy("battery-list"))


"""
class BatteryDeploymentDelete(DeleteView):
    model = models.Battery
    success_url = reverse_lazy('battery-list')
"""


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
        """ we might accept the uuid assocaited with the worker instead of its id """
        self.subject = get_object_or_404(
            models.Subject, pk=self.kwargs.get("subject_id")
        )
        self.battery = get_object_or_404(
            models.Battery, pk=self.kwargs.get("battery_id")
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
