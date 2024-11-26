'''
    Export result data to file system.
    For use by docker-compose via manage.py, update output_dir as needed.
    Example:
    docker-compose -f production.yml run --rm django manage.py shell -c "import from scripts.export_to_file import dump_all; dump_all()"
'''
from datetime import datetime
import ast
import csv
import json
import math
import os

from django.db.models import Count

import experiments.models as em
import prolific.models as pm

output_dir = '/results_export'

def dump_all():
    batteries = em.Battery.objects.all()
    for batt in batteries:
        dump_battery(batt)
    dump_sc_metadata()
    dump_scs_metadata()

def dump_by_id(bid):
    batt = em.Battery.objects.get(id=bid)
    dump_battery(batt)

def dump_battery(battery):
    battery_id = f'battery-{battery.id}'
    os.makedirs(os.path.join(output_dir, battery_id), exist_ok=True)
    manifest = []
    manifest_fname = f"{battery_id}_manifest.csv" 
    try:
        with open(os.path.join(output_dir, battery_id, manifest_fname), "r") as fp:
            csv_reader = csv.reader(fp)
            manifest = [x for x in csv_reader]
    except OSError:
        pass

    dumped_assignment_ids = [int(x[0]) for x in manifest]
    assignments = em.Assignment.objects.filter(
        battery=battery, status="completed"
    ).exclude(id__in=dumped_assignment_ids)

    add_to_manifest = []
    for assignment in assignments:
        dump_assignment(assignment, battery_id)
        add_to_manifest.append([str(assignment.id), datetime.now().isoformat()])

    with open(os.path.join(output_dir, battery_id, manifest_fname), 'a') as fp:
        fp.write('\n'.join(','.join([x for x in add_to_manifest])))

def dump_assignment(assignment, target_dir=None, force=False):
    result_fname = 'sub-{sub}_{batt}_order-{order}_task-{exp_name}_asgn-{aid}_data.json'
    sub = assignment.subject.prolific_id or assignment.subject.id
    results = list(assignment.result_set.all().order_by('completed_at'))
    if not results:
        return
    padding = math.floor(math.log(len(results), 10)) + 1
    for i, result in enumerate(results):
        # innefficent, any way to annotate or lookup in pregenerated list? or just pull from task data...
        exp_name = "none"
        try:
            exp_name = result.battery_experiment.experiment_instance.experiment_repo_id.name
        except:
            pass
        order = str(i).zfill(padding)
        fname = result_fname.format(sub=sub, batt=target_dir, exp_name=exp_name, order=order, aid=assignment.id)
        data = ast.literal_eval(result.data)
        with open(os.path.join(output_dir, target_dir, fname), 'w') as fp:
            json.dump(data, fp)

def dump_sc_metadata():
    fname = 'study_collections.json'
    to_dump = []
    fields = ['id', 'name', 'project', 'workspace_id', 'title', 'description', 'total_available_places', 'estimated_completion_time', 'reward', 'published', 'inter_study_delay', 'active', 'number_of_groups', 'time_to_start_first_study', 'failure_to_start_grace_interval', 'failure_to_start_message', 'failure_to_start_warning_message', 'study_time_to_warning', 'study_warning_message', 'study_grace_interval', 'study_kick_on_timeout', 'collection_time_to_warning', 'collection_warning_message', 'collection_grace_interval', 'collection_kick_on_timeout', 'screener_rejection_message']

    sces = pm.StudyCollection.objects.all().order_by('id')
    for sc in sces:
        entry = {k: sc.__dict__[k] for k in fields}
        if sc.screener_for:
            entry['screeneer_for'] = sc.screener_for.id
        if sc.parent:
            entry['parent'] = sc.parent.id
        if sc.children.all():
            entry['children'] = [x.id for x in sc.children.all()]
        studies = sc.study_set.all().order_by('rank')
        entry['studies'] = []
        for study in studies:
            study_entry = {
                'local_id': study.id,
                'remote_id': study.remote_id,
                'battery': study.battery.id,
                'rank': study.rank,
                'participant_group': study.participant_group,
                'completion_code': study.completion_code
            }
            entry['studies'].append(study_entry)
        to_dump.append(entry)
    with open(os.path.join(output_dir, fname), 'w') as fp:
        json.dump(to_dump, fp, default=lambda x: str(x), indent=2)

def dump_scs_metadata():
    fname = 'sc-{sc_id}.json'
    sces = pm.StudyCollection.objects.all().order_by('id')
    for sc in sces:
        scs_all = sc.studycollectionsubject_set.all() 
        if not scs_all:
            continue
        sc_dump = {}
        sc_dump['subjects'] = []
        statuses = sc.studycollectionsubject_set.all().values('status').annotate(count=Count('status')).order_by().distinct()
        status_counts = {x['status']: x['count'] for x in statuses}
        sc_dump['status_counts'] = status_counts
        for scs in scs_all:
            study_subjects = pm.StudySubject.objects.filter(study__study_collection=scs.study_collection).select_related('study').select_related('assignment').values_list('study__id', 'assignment__id')
            assignments = []
            for ss in study_subjects:
                assignments.append({
                    'study_id': ss[0],
                    'assignment_id': ss[1],
                })
            scs_dump = {
                'subject': scs.subject.prolific_id,
                'assignments': assignments,
                'group_index': scs.group_index,
                'current_battery': scs.current_study.battery.id if scs.current_study else None,
                'status': scs.status, 
                'status_reason': scs.status_reason, 
            }
            time_fields = ['failed_at', 'warned_at', 'ttfs_warned_at', 'ttcc_warned_at', 'ttcc_flagged_at']
            scs_dump.update({x: scs.__dict__[x].isoformat() if scs.__dict__[x] else None for x in time_fields})
            sc_dump['subjects'].append(scs_dump)
        with open(os.path.join(output_dir, fname.format(sc_id=sc.id)), 'w') as fp:
            json.dump(sc_dump, fp, default=lambda x: str(x), indent=2)
