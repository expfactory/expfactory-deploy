from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import View, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from experiments import views as exp_views
from experiments import models as exp_models

from prolific import models
from prolific import forms

class ProlificServe(exp_views.Serve):
    def set_subject(self):
        prolific_id = self.request.GET.get('PROLIFIC_PID')
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

'''
class CollectionView(LoginRequiredMixin, TemplateView):
    template_name = "prolific/collection.html"
    collection = None

    def get_object(self)
        collection_id = self.kwargs.get("collection_id")
        if collection_id is not None:
            self.collection = get_object_or_404(models.Collection, pk=collection_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get(self, request, *args, **kwargs):
        self.get_object()
        context = {}
        context['batteries'] = exp_models.Battery.objects.exclude(status__in=['template', 'inactive']).values_list('id', 'title')
        if self.collection is None:
            # form
        else:
            # form with instance
            # list of existing Studies
            # self.collection.study_set.all()
            # list of their order objects
            # models.StudyRank.objects.filter(study__study_collection=self.collection)

        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        return
'''
