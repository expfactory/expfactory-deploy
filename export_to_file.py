"""
studycollections
    study/battery

manifest.tsv
result_id, datafile

sub-xxx/
    batt-xxx/
        sub-xxx_batt-xxx_order-xxx_task-xxx_data.parquet
        sub-xxx_batt-xxx_order-xxx_task-xxx_data.json
"""


import ast
import csv
import json
import math
import os

import experiments.models as em
import prolific.models as pm

output_dir = "test_to_file"


def dump_all():
    batteries = em.Battery.objects.all()
    for batt in batteries:
        dump_battery(batt)


from string import Template

result_fname = "sub-{sub}_{batt}_order-{order}_task-{exp_name}_data.json"


def dump_battery(battery):
    # sub_ids = assignments.values_list('subject__id', flat=True).distinct()
    # subjects = em.Subject.objects.filter(id__in=sub_ids)
    battery_id = f"battery-{battery.id}"
    os.makedirs(os.path.join(output_dir, battery_id), exist_ok=True)

    manifest = []
    try:
        with open(f"{battery_id}_manifest.csv", "r") as fp:
            csv_reader = csv.reader(fp)
            manifest = [x for x in csv_reader]
    except OSError:
        pass

    dumped_assignment_ids = [int(x[1]) for x in manifest]
    assignments = em.Assignment.objects.filter(
        battery=battery, status="completed"
    ).exclude(id__in=dumped_assignment_ids)
    for assignment in assignments:
        dump_assignment(assignment, battery_id)


def dump_assignment(assignment, battery_id):
    sub = assignment.subject.prolific_id
    results = list(assignment.result_set.all().order_by("completed_at"))
    if not results:
        return
    padding = math.floor(math.log(len(results), 10)) + 1
    for i, result in enumerate(results):
        # innefficent, any way to annotate or lookup in pregenerated list? or just pull from task data...
        exp_name = "none"
        try:
            exp_name = (
                result.battery_experiment.experiment_instance.experiment_repo_id.name
            )
        except:
            pass
        modified = result.modified.isotime()
        data = ast.literal_eval(result.data)
        order = str(i).zfill(padding)
        fname = result_fname.format(
            sub=sub, batt=battery_id, exp_name=exp_name, order=order
        )
        with open(os.path.join(output_dir, battery_id, fname), "w") as fp:
            json.dump(data, fp)
