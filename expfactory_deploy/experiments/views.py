from django.contrib import messages
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


class BatteryCreate(CreateView):
    model = models.Battery
    # fields = [ "name", "consent", "insturctions", "advertisement"]
    form_class = forms.BatteryForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        add_experiment_repos(context)
        context["exp_instance_formset"] = formset_factory(
            forms.ExperimentInstanceForm, can_order=True, can_delete=True
        )
        return context

    def get_initial(self):
        initial = super().get_initial()
        battery_id = self.kwargs.get("battery_id")
        battery = None
        if battery_id:
            battery = models.Battery.objects.get(pk=battery_id)
        if battery:
            for field in fields:
                if battery.get(field):
                    initial[field] = battery[field]


class BatteryComplex(TemplateView):
    template_name = "experiments/battery_form.html"
    battery = None
    battery_kwargs = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        battery_id = self.kwargs.get("pk")
        battery = None
        ordering = None
        initial = None
        if self.battery:
            ordering = (
                self.battery.batteryexperiments_set.all()
                .order_by("order")
                .prefetch_related("experiment_instance")
            )
            initial = [{order: x.order, **x.experiment_instance} for x in ordering]

        context["form"] = forms.BatteryForm(**self.battery_kwargs)

        add_experiment_repos(context)
        # context["exp_instance_formset"] = forms.ExpInstanceFormset(queryset=models.ExperimentInstance.objects.none())
        context["exp_instance_formset"] = forms.ExpInstanceFormset()
        return context

    def get_object(self):
        battery_id = self.kwargs.get("battery_id")
        if battery_id is not None:
            battery = get_object_or_404(models.Battery, pk=battery_id)
            self.battery = battery
            self.battery_kwargs = {instance: battery}

    """Render a form on GET and processes it on POST."""

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        self.get_object()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.get_object()
        form = forms.BatteryForm(self.request.POST, **self.battery_kwargs)
        battery = form.save()

        exp_instance_formset = forms.ExpInstanceFormset(self.request.POST)
        # exp_instances = exp_instance_formset.save(commit=False)
        valid = exp_instance_formset.is_valid()
        if valid:
            for order, form in enumerate(exp_instance_formset.ordered_forms):
                exp_inst = form.save()
                models.BatteryExperiments.objects.create(
                    battery=battery, experiment_instance=exp_inst, order=order
                )
        if form.is_valid():
            return HttpResponseRedirect("/battery/")
        else:
            return HttpResponseRedirect(reverse_lazy("battery-list"))


class BatteryUpdate(UpdateView):
    model = models.Battery
    # fields = ["name", "consent", "insturctions", "advertisement"]
    form = forms.BatteryForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        add_experiment_repos(context)
        return context


"""
class BatteryDeploymentDelete(DeleteView):
    model = models.Battery
    success_url = reverse_lazy('battery-list')
"""
