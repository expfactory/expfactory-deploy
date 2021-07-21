from django.forms import ModelForm

from experiments import models as models

'''
class BatteryDeploymentForm(ModelForm):
    class Meta:
        model = models.BatteryDeployment
        fields = [
            "name", "battery_id", "consent",
            "insturctions", "advertisement"
        ]

    # For now we will just default to the latest commits from experiments
    #    used by the parent battery if its ID happens to be set in URL
    def save(self, commit=True):
        battery_deployment = self.super().save(commit=False)
        battery_id = self.kwargs.get('battery_id')
        battery = Battery.objects.get(pk=battery_id)
        if parent_battery:
            battery_deployment.battery_id = parent_battery.id
            for experiment in parent_battery.experiments.all():
                exp_instance, created = ExperimentInstance.get_or_create(
                    experiment_repo_id=experiment.id,
                    commit="latest"
                )
                battery_deployment.experiment_instances.add(exp_instance)
        if commit:
            battery_deployment.save()
        return battery_deployment
'''
