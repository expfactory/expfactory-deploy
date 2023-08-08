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
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from taggit.models import Tag

from experiments import forms as forms
from experiments import models as models
from experiments.utils.repo import find_new_experiments, get_latest_commit
from experiments.utils.assignments import batch_assignments
from experiments.utils.export import export_battery, export_subject, export_single_result

from prolific.models import SimpleCC

sys.path.append(str(Path(settings.ROOT_DIR, "expfactory_deploy_local/src/")))

from expfactory_deploy_local.utils import generate_experiment_context

# Repo Views

class RepoOriginList(LoginRequiredMixin, ListView):
    model = models.RepoOrigin
    queryset = models.RepoOrigin.objects.prefetch_related("experimentrepo_set")

class RepoOriginDetail(LoginRequiredMixin, DetailView):
    model = models.RepoOrigin
    queryset = models.RepoOrigin.objects.prefetch_related("experimentrepo_set")

class RepoOriginCreate(LoginRequiredMixin, CreateView):
    model = models.RepoOrigin
    form_class = forms.RepoOriginForm
    success_url = reverse_lazy("experiments:experiment-repo-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.clone()
        return response

class RepoOriginPull(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        for repo in models.RepoOrigin.objects.filter(active=True):
            repo.pull_origin()
        return redirect("experiments:experiment-repo-list")

# Experiment Views
def experiment_instances_from_latest(experiment_repos):
    for experiment_repo in experiment_repos:
        latest = get_latest_commit(experiment_repo.location)
        models.ExperimentInstance.get_or_create(
            experiment_repo_id=experiment_repo.id, commit=latest
        )
        return reverse_lazy("experiments:experiment-repo-list")


class ExperimentRepoDetail(LoginRequiredMixin, ListView):
    model = models.ExperimentRepo
    queryset = models.ExperimentRepo.objects.prefetch_related("origin", "tags").filter(origin__active=True).order_by('name')

class ExperimentRepoList(LoginRequiredMixin, ListView):
    model = models.ExperimentRepo
    queryset = models.ExperimentRepo.objects.prefetch_related("origin", "tags").filter(origin__active=True).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = [x['name'] for x in Tag.objects.all().values('name')]
        tags.append('')
        context['tags'] = tags
        context['tag_form'] = forms.ExperimentRepoBulkTagForm()
        context['origins'] = models.RepoOrigin.objects.filter(active=True)
        return context

class ExperimentRepoDetail(LoginRequiredMixin, DetailView):
    model = models.ExperimentRepo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batteries = models.Battery.objects.filter(batteryexperiments__experiment_instance__experiment_repo_id=self.get_object())
        results = models.Result.objects.filter(battery_experiment__experiment_instance__experiment_repo_id=self.get_object())
        batt_results = [(batt, list(results.filter(battery_experiment__battery=batt))) for batt in batteries]
        context['batt_results'] = batt_results
        return context


@login_required
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

class ExperimentRepoUpdate(LoginRequiredMixin, UpdateView):
    model = models.ExperimentRepo
    form_class = forms.ExperimentRepoForm
    success_url = reverse_lazy("experiments:experiment-repo-list")

class ExperimentRepoDelete(LoginRequiredMixin, DeleteView):
    model = models.ExperimentRepo
    success_url = reverse_lazy("experiments:experiment-repo-list")

class ExperimentInstanceCreate(LoginRequiredMixin, CreateView):
    model = models.ExperimentInstance
    form_class = forms.ExperimentInstanceForm
    success_url = reverse_lazy("experiments:experiment-instance-detail")

class ExperimentInstanceUpdate(LoginRequiredMixin, UpdateView):
    model = models.ExperimentInstance
    form_class = forms.ExperimentInstanceForm
    success_url = reverse_lazy("experiments:experiment-instance-detail")

class ExperimentInstanceDetail(LoginRequiredMixin, DetailView):
    model = models.ExperimentInstance

'''
    This is called via HTMX when a new experiment_instance is selected from
    the drop down in the form, or an experiment_repo is dragged over to the
    batteries current experiments colomn. In the case of the select HTMX
    encodes the select value as a query param whose key is the html `name`
    attribute. The value changes since the form is part of a formset, but
    always ends with the same value, this is retrieved with the next iterator
    call.
'''
def instance_order_form(request, *args, **kwargs):
    repo_id = kwargs.get("repo_id", -1)
    params = request.GET.items()
    instance_id = next((x[1] for x in params if x[0].endswith("exp_instance_select")), None)

    if instance_id is None:
        form = forms.ExperimentInstanceOrderForm(repo_id=repo_id)
    elif instance_id is not None:
        instance = models.ExperimentInstance.objects.get(id=instance_id)
        form = forms.ExperimentInstanceOrderForm(instance=instance, repo_id=repo_id)
    return render(request, "experiments/experimentinstance_form.html", {"form": form, "text": "wat"})

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


class BatteryList(LoginRequiredMixin, ListView):
    model = models.Battery

    def get_queryset(self):
        status = self.kwargs.get('status', 'template')
        return models.Battery.objects.filter(status=status).prefetch_related("children")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        statuses = [x[0] for x in self.model.STATUS]
        context['statuses'] = statuses
        for battery in context['object_list']:
            if self.kwargs.get('status', None) != 'inactive':
                battery.active_children = battery.children.exclude(status='inactive')
        return context


class BatteryDetail(LoginRequiredMixin, DetailView):
    model = models.Battery
    queryset = models.Battery.objects.prefetch_related("assignment_set", "experiment_instances")
    context_object_name = "battery"


"""
    View used for battery creation. Handles creating expdeirmentinstance
    objects and order entries in the battery <-> experiment instance pivot table
    as needed.
"""
class BatteryComplex(LoginRequiredMixin, TemplateView):
    template_name = "experiments/battery_form.html"
    battery = None
    battery_kwargs = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = models.ExperimentInstance.objects.none()
        ordering = None
        if self.battery:
            qs = models.ExperimentInstance.objects.filter(battery=self.battery).order_by('batteryexperiments__order').all()
            ordering = qs.annotate(exp_order=F('batteryexperiments__order'))
            context['battery'] = self.battery
        if "form" not in kwargs:
            context["form"] = forms.BatteryForm(**self.battery_kwargs)
        else:
            context["form"] = kwargs.get("form")

        if "exp_instance_formset" not in kwargs:
            context["exp_instance_formset"] = forms.ExpInstanceFormset(
                queryset=qs, form_kwargs={"ordering": ordering}
            )
        else:
            context["exp_instance_formset"] = kwargs.get("exp_instance_formset")

        add_experiment_repos(context, self.battery)

        '''
            We could attempt to seperate out ordering (handled as a
            BatteryExperiment) and ExperimentInstance creation.
        context["test_exp_instance_formset"] = forms.TestExpInstanceFormset(
            queryset=qs
        )
        context["battery_experiments_formset"] = forms.BatteryExperimentsFormset(
            queryset=self.battery.batteryexperiments_set.all()
        )
        '''
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

        '''
        ordering = models.ExperimentInstance.objects.filter(
            batteryexperiments__battery=self.battery
        ).order_by("batteryexperiments__order")
        '''
        exp_instance_formset = forms.ExpInstanceFormset(
            self.request.POST, form_kwargs={"battery_id": battery.id}
        )
        valid = exp_instance_formset.is_valid()
        if valid:
            ei = exp_instance_formset.save()
            battery.batteryexperiments_set.exclude(experiment_instance__in=ei).delete()
        elif not valid:
            print(exp_instance_formset.errors)
            return self.render_to_response(self.get_context_data(form=form, exp_instance_formset=exp_instance_formset))

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
    return HttpResponseRedirect(reverse_lazy("experiments:battery-detail", kwargs={'pk':pk}))

@login_required
def publish_battery_confirmation(request, pk):
    battery = get_object_or_404(models.Battery, pk=pk)
    return render(request, 'experiments/battery_publish_confirmation.html', {'battery': battery})

@login_required
def deactivate_battery(request, pk):
    referer = request.META.get("HTTP_REFERER")
    battery = get_object_or_404(models.Battery, pk=pk)
    if battery.status == "template":
        for child in battery.children.all():
            child.status = "inactive"
            child.save()
    battery.status = "inactive"
    battery.save()
    # return HttpResponseRedirect(referer)
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
    return render(request, 'experiments/repo_deactivate_confirmation.html', {'repo': repo})

@login_required
def batch_assignment_create(request, battery_id, num_subjects):
    battery = get_object_or_404(models.Battery, pk=battery_id)
    urls = batch_assignments(battery, num_subjects)
    response = render(request, 'experiments/assignment_urls.txt', {'urls': urls}, content_type='text/plain')
    fname = f'batch_assignments_{datetime.now().strftime("%Y.%m.%d.%H%M%S")}.txt'
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    return response

class BatteryClone(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        batt = get_object_or_404(models.Battery, pk=pk)
        new_batt = batt.duplicate()
        new_batt.status = 'draft'
        new_batt.save()
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
    origin_path = exp_instance.experiment_repo_id.origin.path
    exp_fs_path = Path(location.replace(origin_path, deploy_static_fs))
    exp_url_path = Path(location.replace(origin_path, deploy_static_url))

    # default js/css location for poldracklab style experiments
    static_url_path = Path(settings.STATIC_NON_REPO_URL, "default")

    return generate_experiment_context(
        exp_fs_path, static_url_path, exp_url_path
    )

class Preview(View):
    def get(self, request, *args, **kwargs):
        exp_id = self.kwargs.get("exp_id")
        experiment = get_object_or_404(models.ExperimentRepo, id=exp_id)
        commit = self.kwargs.get("commit", experiment.get_latest_commit())

        exp_instance, created = models.ExperimentInstance.objects.get_or_create(
            experiment_repo_id=experiment, commit=commit
        )

        template = "experiments/jspsych_deploy.html"
        context = jspsych_context(exp_instance)
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        return HttpResponse(request.body)


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

class Serve(View):
    subject = None
    battery = None
    experiment = None
    assignment = None

    def set_subject(self):
        subject_id = self.kwargs.get("subject_id")
        """ we might accept the uuid assocaited with the subject instead of its id """
        if subject_id is not None:
            self.subject = get_object_or_404(
                models.Subject, id=subject_id
            )
        else:
            self.subject = None

    def set_battery(self):
        battery_id = self.kwargs.get("battery_id")
        self.battery = get_object_or_404(
            models.Battery, id=battery_id
        )

    def set_assignment(self):
        # When might we want to error out instead of just create assignment?
        self.assignment = models.Assignment.objects.get_or_create(subject=self.subject, battery=self.battery)[0]

    def complete(self, request):
        try:
            cc = SimpleCC.objects.get(battery=self.battery)
            return render(request, "prolific/complete.html", {'completion_url': cc.completion_url})
        except ObjectDoesNotExist:
            return redirect(reverse('experiments:complete'))

    def set_experiment(self):
        experiment_id = self.kwargs.get("experiment_id")
        if experiment_id is not None:
            self.experiment = get_object_or_404(
                models.BatteryExperiment,
                id=experiment_id
            )

    def get(self, request, *args, **kwargs):
        self.set_subject()
        self.set_battery()
        self.set_assignment()
        self.set_experiment()

        if self.assignment.consent_accepted is not True and self.battery.consent:
            return redirect(reverse("experiments:consent", kwargs={'assignment_id': self.assignment.id}))
            '''
            context = {
                'consent': self.battery.consent,
                'instructions': self.battery.instructions
            }
            return render(request, "experiments/instructions.html", context)
            '''

        self.experiment, num_left = self.assignment.get_next_experiment()

        if self.experiment is None:
            return self.complete(request)

        exp_context = jspsych_context(self.experiment)
        exp_context["post_url"] = reverse_lazy("experiments:push-results", args=[self.assignment.id, self.experiment.id])
        # No longer in use. We just location.reload for experiments.
        # exp_context["next_page"] = reverse_lazy("experiments:serve-battery", args=[self.subject.id, self.battery.id])

        # We could insert this into finish message
        # exp_context["num_left"] = num_left
        exp_context["exp_config"] = {}
        context = {**exp_context}
        return render(request, "experiments/jspsych_deploy.html", context)

class ServeConsent(View):
    preview = False
    battery = None

    def get_context_data(self, **kwargs):
        if (self.preview):
            self.battery = get_object_or_404(
                models.Battery,
                id=self.kwargs.get('battery_id')
            )
            next_url = reverse('experiments:battery-detail', kwargs={'pk': self.battery.id})
        else:
            assignment = get_object_or_404(
                models.Assignment,
                id=self.kwargs.get('assignment_id')
            )
            self.battery = assignment.battery
            next_url = reverse('experiments:consent', kwargs={'assignment_id': assignment.id})

        return {
            'consent': self.battery.consent,
            'instructions': self.battery.instructions,
            'next_url': next_url
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        form = forms.ConsentForm()
        if (self.preview):
            form.helper.form_action = reverse('experiments:battery-detail', kwargs={'pk': self.battery.id})
            form.helper.form_method = 'post'
        context['consent_form'] = form

        return render(request, "experiments/instructions.html", context)

    def post(self, request, *args, **kwargs):
        assignment = get_object_or_404(
            models.Assignment,
            id=self.kwargs.get('assignment_id')
        )
        consent_form = forms.ConsentForm(request.POST)
        if consent_form.is_valid():
            assignment.consent_accepted = consent_form.cleaned_data['accept']
            if assignment.consent_accepted and assignment.status == 'not-started':
                assignment.status = 'started'
            assignment.save()
            if assignment.consent_accepted:
                return redirect(reverse(
                    'experiments:serve-battery',
                    kwargs={'subject_id': assignment.subject.id, 'battery_id': assignment.battery.id}
                ))
            elif assignment.consent_accepted is False:
                assignment.status = 'failed'
                assignment.save()
                return redirect(reverse('experiments:decline'))
        else:
            return self.get(request, *args, **kwargs)

class PreviewConsent(ServeConsent):
    preview = True

'''
View for participants to push data to.
'''
class Results(View):
    # If more frameworks are added this would dispatch to their respective
    # versions of this function.
    # expfactory-docker purges keys and process survey data at this step
    def process_exp_data(self, post_data, assignment):
        data = json.loads(post_data)
        finished = data.get("status") == "finished"
        if assignment.status == "not-started":
            assignment.status = "started"
        if assignment.prolific_id != None and data.get('prolific_id') is None:
            data['prolific_id'] = assignment.prolific_id
        return data, finished

    def post(self, request, *args, **kwargs):
        print(request.body)
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

class SubjectDetail(LoginRequiredMixin, DetailView):
    model = models.Subject

class SubjectList(LoginRequiredMixin, ListView):
    model = models.Subject
    queryset = models.Subject.objects.filter(active=True).prefetch_related("assignment_set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject_select'] = forms.SubjectActionForm()
        return context

class CreateSubjects(LoginRequiredMixin, FormView):
    template_name = 'experiments/create_subjects.html'
    form_class = forms.SubjectCount
    success_url = reverse_lazy('experiments:subject-list')
    def form_valid(self, form):
        new_subjects = [models.Subject() for i in range(form.cleaned_data['count'])]
        models.Subject.objects.bulk_create(new_subjects)
        return super().form_valid(form)

class SubjectListAction(LoginRequiredMixin, FormView):
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

class ExperimentRepoBulkTag(LoginRequiredMixin, FormView):
    form_class = forms.ExperimentRepoBulkTagForm
    template_name = 'experiments/experimentrepo_list.html'
    success_url = reverse_lazy('experiments:experiment-repo-list')
    def form_valid(self, form):
        exp_repos = models.ExperimentRepo.objects.filter(id__in=form.cleaned_data['experiments'])
        action = self.kwargs.get('action')
        for exp_repo in exp_repos:
            if action == 'add':
                exp_repo.tags.add(*form.cleaned_data['tags'])
            elif action == 'remove':
                exp_repo.tags.remove(*form.cleaned_data['tags'])
            exp_repo.save()
        return super().form_valid(form)

'''
Following four are for downloaing results, not posting them to them to server
'''
class ResultDetail(LoginRequiredMixin, DetailView):
    model = models.Result
    content_type = 'text/html'
    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        response['Content-Disposition'] = f'attachment; filename="result_{self.object.pk}.txt"'
        return response

@login_required
def single_result(request, result_id):
    result = get_object_or_404(models.Result, pk=result_id)
    results = export_single_result(result_id)
    response = JsonResponse(results)
    fname = f'result_{result.id}_{datetime.now().strftime("%Y.%m.%d.%H%M%S")}.json'
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    return response

@login_required
def battery_results(request, battery_id):
    battery = get_object_or_404(models.Battery, pk=battery_id)
    results = export_battery(battery_id)
    response = JsonResponse(results)
    fname = f'battery_{battery.id}_{datetime.now().strftime("%Y.%m.%d.%H%M%S")}.json'
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    return response

@login_required
def subject_results(request, subject_id):
    subject = get_object_or_404(models.Subject, pk=subject_id)
    results = export_subject(subject_id)
    response = JsonResponse(results)
    fname = f'subject_{subject.__str__()}_{datetime.now().strftime("%Y.%m.%d.%H%M%S")}.json'
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    return response

class Complete(TemplateView):
    template_name = 'experiments/complete.html'

class Decline(TemplateView):
    template_name = 'experiments/decline.html'
