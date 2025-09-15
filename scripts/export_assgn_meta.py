'''
    Alternative attempt to dump metadata to a single file
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

header = [
    'subject',
    'battery_id',
    'assgn_id',
    'study_local_id',
    'alt_id',
    'study_prolific_id',
    'study_collection_id',
    'participant_group',
    'group_index',
    'modified',
    'completed',
    'exp_status',
    'assgn_status',
    'exp_name',
    'fname',
]

to_export = []
missing_study = []
multiple_ss = []
res_issue = []
scs_issue = []
uses_alt_id = []

def write_globals(output_dir):
    with open(os.path.join(output_dir, 'multiple_ss.txt'), 'w') as fp:
        fp.write(str(multiple_ss))
    with open(os.path.join(output_dir, 'missing_study.txt'), 'w') as fp:
        fp.write(str(missing_study))
    with open(os.path.join(output_dir, 'res_issue.txt'), 'w') as fp:
        fp.write(str(res_issue))
    with open(os.path.join(output_dir, 'scs_issue.txt'), 'w') as fp:
        fp.write(str(scs_issue))
    with open(os.path.join(output_dir, 'uses_alt_id.txt'), 'w') as fp:
        fp.write(str(uses_alt_id))
    with open(os.path.join(output_dir, 'unified.csv'), 'w') as fp:
        csv.writer(fp).writerow(header)
        csv.writer(fp).writerows(to_export)

def aid_to_fname(dir):
    fname_lookup = {}
    for entry in os.scandir(dir):
        if entry.is_dir():
           fname_lookup.update(aid_to_fname(entry.path))
        if entry.is_file():
            if '_asgn-' in entry.path:
                assgn_id = int(entry.name.split('_asgn-')[1].split('_')[0])
                exp_name = entry.name.split('task-')[1].split('_asgn')[0]
                battery_id = entry.path.split('/battery-')[1].split('/')[0]
                fname_lookup[(assgn_id, exp_name)] = os.path.join(f"battery-{battery_id}/", entry.name)

    return fname_lookup

def collect_all_assgn_metadata(results_dir=None):
    assignments = em.Assignment.objects.filter(subject__prolific_id__isnull=False)
    # assignments = em.Assignment.objects.filter(subject__prolific_id="6700975875a6b9761e760c50")
    fname_lookup = aid_to_fname(results_dir) if results_dir else None

    for assgn in assignments:
        collect_assignment_metadata(assgn, fname_lookup)
    if results_dir:
        write_globals(results_dir)

def collect_assignment_metadata(assgn, fname_lookup=None):
    subject = assgn.subject
    results = assgn.result_set.all()
    battery_id = assgn.battery.id
    assgn_id = assgn.id
    alt_id = assgn.alt_id
    ss = None
    study = None
    try:
        ss = pm.StudySubject.objects.get(assignment=assgn)
        study = ss.study
    except pm.StudySubject.DoesNotExist:
        # print(f'No ss for {assgn.id}')
        pass
    except pm.StudySubject.MultipleObjectsReturned:
        multiple_ss.append(assgn.id)
        return

    try:
        if ss is None:
            study = pm.Study.objects.get(remote_id=alt_id)
            uses_alt_id.append(assgn.id)
    except Exception as e:
        missing_study.append(assgn_id)
        return

    study_local_id = study.id
    study_prolific_id = study.remote_id
    study_collection_id = study.study_collection.id
    rank = study.rank
    participant_group = study.participant_group
    group_index = "None"
    try:
        scs = pm.StudyCollectionSubject.objects.get(subject=subject, study_collection=study.study_collection)
        group_index = scs.group_index
    except:
        scs_issue.append((subject.id, study.study_collection.id))

    for res in results:
        try:
            exp_name = res.battery_experiment.experiment_instance.experiment_repo_id.name
            modified = res.modified.isoformat() if res.modified else None
            completed = res.completed_at.isoformat() if res.completed_at else None
        except:
            res_issue.append(res.id)
            continue
        fname = fname_lookup.get((assgn_id, exp_name), "None") if fname_lookup else "None"
        exp_status = res.status
        assgn_status = assgn.status
        to_export.append([
            subject,
            battery_id,
            assgn_id,
            study_local_id,
            alt_id,
            study_prolific_id,
            study_collection_id,
            participant_group,
            group_index,
            modified,
            completed,
            exp_status,
            assgn_status,
            exp_name,
            fname,
        ])
