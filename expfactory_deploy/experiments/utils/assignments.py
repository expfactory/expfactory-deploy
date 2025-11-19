from django.conf import settings
from django.urls import reverse

from experiments import models as models

def batch_assignments(battery, num_subjects=1):
    urls = []
    for i in range(num_subjects):
        subject = models.Subject()
        subject.save()
        assignment = models.Assignment(subject=subject, battery=battery)
        assignment.save()
        urls.append(f'{settings.BASE_URL}{reverse("experiments:serve-battery", args=[subject.pk, battery.pk])}')
    return urls

def check_assignment_status(assignment):
    import ast
    from pprint import pprint
    from experiments import models as em
 
    results = em.Result.objects.filter(assignment=assignment)
    result_errors = []
 
    batt_exp_ids = em.BatteryExperiments.objects.filter(battery=assignment.battery).values_list('id', flat=True)
    res_exp_ids = []
    for result in results:
        data = ast.literal_eval(result.data)
        data_status = data.get('status')
        if data_status == 'finished' and result.status != 'completed':
            result_errors.append(result.id)
        res_exp_ids.append(result.battery_experiment_id)
 
    unexpected_exp = [id for id in res_exp_ids if id not in batt_exp_ids]
    missing_exp = [id for id in batt_exp_ids if id not in res_exp_ids]
 
    if not missing_exp and assignment.status != 'completed':
        print(f'assignment {assignment.id} is marked as {assignment.status} but should be complete')
 
    report = dict(
        subject=assignment.subject,
        result_errors=result_errors,
        unexpected_exp=unexpected_exp,
        missing_exp=missing_exp
    )
    pprint(report)
