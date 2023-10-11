import json
import os
from functools import wraps

from django.conf import settings

from pyrolific import Client, AuthenticatedClient
from pyrolific import models as api_models
from pyrolific.api.studies import (
    get_studies,
    get_project_studies,
    get_study,
    publish_study,
    update_study,
    create_study
)

from pyrolific.api.participant_groups import (
    add_to_participant_group,
    get_participant_group_participants,
    create_participant_group,
    get_participant_group,
    remove_from_participant_group,
    delete_participant_group,
    get_participant_groups,
    update_participant_group
)

from pyrolific.api.submissions import (
    get_submissions,
    get_submission
)
from pyrolific.api import studies
token = settings.PROLIFIC_KEY

client_kwargs = {
    'authorization': f"Token {token}",
    'client': Client(base_url="https://api.prolific.com")
}

auth_client = AuthenticatedClient(base_url="https://api.prolific.com", token=token, prefix="Token")

class NoProlificKeyException(Exception):
    pass

class GenericProlificException(Exception):
    pass

def api_client(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if token is None:
            raise NoProlificKeyException
        return f(*args, **kwds)
    return wrapper

''' Api Documentation doesn't suggest pagination on this endpoint but api response
    has fields for it. Haven't seen it used so far. '''
def make_call(api_func, ac=False, **kwargs):
    if ac:
        response = api_func.sync_detailed(client=auth_client, **kwargs)
    else:
        response = api_func.sync_detailed(**kwargs, **client_kwargs)
    if response.status_code.value > 399:
        print(response)
        return response
        # raise GenericProlificException(response.status)
    response = response.parsed.to_dict()
    if 'links' in response and response['_links']['next']['href'] is not None:
        raise GenericProlificException("Next link found, implement pagination")
    return response

def list_studies(pid=None):
    if pid:
        response = make_call(get_project_studies, project_id=pid)
    else:
        response = make_call(get_studies)
    if hasattr(response, 'status_code'):
        return []
    return [x for x in response.get('results', [])]

def study_detail(id):
    response = make_call(get_study, id=id)
    return response

def create_draft(study_details):
    to_create = api_models.CreateStudy.from_dict(study_details)
    response = make_call(create_study, json_body=to_create)
    return response

def create_part_group(pid, name):
    to_create = api_models.CreateParticipantGroupJsonBody.from_dict({'project_id': pid, 'name': name})
    response = make_call(create_participant_group, ac=True, json_body=to_create)
    return response

def add_to_part_group(group_id, part_ids):
    to_add = api_models.ParticipantIDList.from_dict({'participant_ids': part_ids})
    response = make_call(add_to_participant_group, ac=True, id=group_id, json_body=to_add)
    return response

def get_participants(gid):
    response = make_call(get_participant_group_participants, ac=True, id=gid)
    return response

''' Response to publish call puts studies in a state called 'PUBLISHING' that the api library doesn't know about.
    We will assume any ValueError is this.
'''
def publish(sid):
    action = api_models.study_transition.StudyTransition("publish")
    try:
        response = make_call(publish_study, id=sid, json_body=action)
    except ValueError as e:
        print(f'publishing {sid} to prolific got valueerror {e}')
        return {}
    return response

def list_submissions(sid=None):
    response = make_call(get_submissions, study=sid)
    if hasattr(response, 'status_code'):
        raise GenericProlificException()
    return response['results']
