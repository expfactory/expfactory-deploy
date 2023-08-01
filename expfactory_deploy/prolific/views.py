from django.shortcuts import get_object_or_404, render, redirect
from django.views import CreateView, UpdateView, View

from experiments import views as exp_views
from experiments import models as exp_models

from prolific import models as models

class ProlificServe(exp_views.Serve):
    def set_subject(self):
        prolific_id = self.request.GET.get('PROLIFIC_ID')
        self.subject = exp_models.Subject.objects.get_or_create(prolific_id=prolific_id)

    def complete(self):
        return redirect('prolific:complete', assignment_id=self.assignment)

class ProlificComplete(View):
    def get(self, request, *args, **kwargs):
        assignment = get_object_or_404(
            models.Assignment,
            id=self.kwargs.get('assignment_id')
        )
        context = {}
        try:
            cc = models.SimpleCC.objects.get(battery=assignment.battery)
            context['CC_url'] = cc.completion_url
        except MyModel.DoesNotExist:
            context['CC_url'] = None

        return render(request, "prolific/complete.html", context)

class SimpleCCCreate(CreateView):
    model = models.SimpleCC
    fields = ["completion_url"]

    def form_valid(self, form):
        battery = get_object_or_404(exp_models.Battery, self.kwargs.get('battery_id'))
        form.instance.battery = battery
        return super().form_valid(form)

class SimpleCCUpdate(UpdateView):
    model = models.SimpleCC
    fields = ["completion_url"]
