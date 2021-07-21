# from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from experiments import models as models
from experiments import forms as forms
from experiments.utils.repo import find_new_experiments, get_latest_commit

# Experiment Views

def experiment_instances_from_latest(experiment_repos):
    for experiment_repo in experiment_repos:
        latest = get_latest_commit(experiment_repo.location)
        ExperimentInstance.get_or_create(
            experiment_repo_id=experiment_repo.id,
            commit=latest
        )

class ExperimentRepoList(ListView):
    model = models.ExperimentRepo
    queryset = models.ExperimentRepo.objects.prefetch_related('origin')


class ExperimentRepoDetail(DetailView):
    model = models.ExperimentRepo

def add_new_experiments(request):
    created_repos, created_experiments = find_new_experiments()
    for repo in created_repos:
        messages.info(request, f"Tracking previously unseen repository {repo.origin}")
    for experiment in created_experiemtns:
        messages.info(request, f"Added new experiment {experiment.name}")
    return reverse_lazy('experiment-repo-list')

class ExperimentRepoUpdate(UpdateView):
    model = models.ExperimentRepo
    fields = ['name']

class ExperimentRepoDelete(DeleteView):
    model = models.ExperimentRepo
    success_url = reverse_lazy('expeirment-repo-list')


# Battery Views

# Inject list of experiment repos into a context and the id attribute used by the form
def add_experiment_repos(context):
    context['experiment_repo_list'] = models.ExperimentRepo.objects.all()
    context['exp_repo_select_id'] = "place_holder"

class BatteryList(ListView):
    model = models.Battery

class BatteryDetail(DetailView):
    model = models.Battery

class BatteryCreate(CreateView):
    model = models.Battery
    fields = ['name', 'experiment_instances', 'consent', 'insturctions', 'advertisement']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        add_experiment_repos(context)
        return context

    def get_initial(self):
        initial = super().get_initial()
        battery_id = self.kwargs.get('battery_id')
        battery = None
        if battery_id:
            battery = models.Battery.objects.get(pk=battery_id)
        if battery:
            for field in fields:
                if battery.get(field):
                    initial[field] = battery[field]


class BatteryUpdate(UpdateView):
    model = models.Battery
    fields = ['name', 'experiments', 'consent', 'insturctions', 'advertisement']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        add_experiment_repos(context)
        return context

'''
class BatteryDeploymentDelete(DeleteView):
    model = models.Battery
    success_url = reverse_lazy('battery-list')
'''
