import ast
import math
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.db.models import F

from experiments import models as models

'''
These functions were written for direct text file downloads of results.
Much of it is reproduced in api_views.
'''

def export_battery(battery_id):
    results = models.Result.objects.filter(battery_experiment__battery=battery_id)
    return export_results(results)

def export_subject(subject_id):
    results = models.Result.objects.filter(subject=subject_id)
    return export_results(results)

def export_single_result(result_id):
    results = models.Result.objects.filter(id=result_id)
    return export_results(results)

def export_results(results):
    res_by_task = defaultdict(list)
    for result in results:
        name = result.battery_experiment.experiment_instance.experiment_repo_id.name
        data = task_data(result.data)
        res_by_task[name].append({'subject': result.subject.__str__(), 'data': data})
    return res_by_task

'''
    This is being done in api_views. Keeping this here in case we want to centralize
    this queryset logic for use by other export methods (to file)

def export_sc(sc_id=None, battery_id=None, subject_id=None):
    qs = em.Result.objects
    if scs_id:
        qs = qs.filter(assignment__battery__study__study_collection__id=sc_id)
    if battery_id:
        qs = qs.filter(assignment__battery__id=battery_id)
    if subject_id:
        qs = qs.filter(assignment__subject__id=subject_id)
    if not (sc_id or battery_id or subject_id):
        qs.all()

    qs.values(id, data).annotate(
        study_collection_id=F("assignment__battery__study__study_collection__id"),
        study_collection_name=F("assignment__battery__study__study_collection__name"),
        battery_name=F("assignment__battery__title"),
        battery_id=F("assignment__battery__id"),
        exp_name=F("battery_experiment__experiment_instance__experiment_repo_id__name"),
        prolific_id=F("assignment__subject__prolific_id"),
    )
    columns = ["id", "study_collection_id", "study_collection_name", "battery_name", "battery_id", "exp_name", "prolific_id", "data"]
'''


'''
playing around with a bidsish export
def export_battery(bid):
    ds = {}
    # assume only one experiment_repo for now.
    tasks = models.ExperimentInstance.objects.filter(battery=bid)
    for task in tasks:
        ds[f'task-{task.experiment_repo_id.name}.json'] = task_serializer(task)
    results = models.Result.objects.filter(battery_experiment__battery=bid)
    subjects =  models.Result.objects.filter(battery_experiment__battery=bid).values_list('subject').distinct()
    subjects = [x[0] for x in subjects]
    padding = math.floor(math.log(len(subjects), 10)) + 1

    participants = [['participant_id', 'uuid']]
    ds['participants.tsv'] = participants
    for subject in subjects:
        sid = f'sub-{subject:0{padding}}'
        participants.append([sid, subject.__str__()])
        beh = {}
        ds[sid] = {'beh': beh}
        results = models.Result.objects.filter(subject=subject, battery_experiment__battery=bid)
        for result in results:
            task_name = result.battery_experiment.experiment_instance.experiment_repo_id.name
            beh_fname = f'{sid}_task-{task_name}_beh.json'
            beh[beh_fname] = task_data(result.data)
    return ds
'''

def task_serializer(task):
   return {
        'commit': task.commit,
        'url': task.experiment_repo_id.url,
        # note?
    }

def task_data(data):
    try:
        data_ast = ast.literal_eval(data)
        return json.dumps(data_ast)
    except:
        return data
