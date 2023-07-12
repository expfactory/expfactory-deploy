from django.views import View
from experiments import views as exp_views

class ProlificServeConsent(exp_views.ServeConsent):
    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        '''
        get prolific id
        get deployment_id
        if per subject deployment
            create study for next experiment.
            study serve url could be assignment_id/experiment_id/study_id
            return study complete url...
        else
            serve timestamp aware study
        '''

'''
special serve, coming from prolific link for specific experiment.
'''
class ProlificServe(exp_views.Serve):
    def get(self, request, *args, **kwargs):
        exp_context = jspsych_context(expid)
        exp_context["post_url"] = reverse_lazy("experiments:push-results", args=[self.assignment.id, self.experiment.id])
        exp_context["next_page"] = reverse_lazy("prolific:complete", args=[])
        context = {**self.get_context_data(), **exp_context}
        return render(request, "experiments/jspsych_deploy.html", context)

class ProlificComplete(View):
    def get(self, request, *args, **kwargs):
        # get study completion url
        # create new study for next experiment.
        context = {
            **self.get_context_data(),
        }
        return render(request, "prolific/complete.html", context)
