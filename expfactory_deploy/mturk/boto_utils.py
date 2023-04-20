from collections import defaultdict
import botocore
import boto3
import re
from datetime import datetime, timedelta
from dateutil.tz import tzlocal

# botocore exceptions

endpoint_url = {
    "sandbox": "https://mturk-requester-sandbox.us-east-1.amazonaws.com",
    "production": "https://mturk-requester.us-east-1.amazonaws.com",
}

url_pattern = r"(?:<ExternalURL>)(?P<url>.*)(?:<\/ExternalURL>)"


# template from boto2
# https://github.com/boto/boto/blob/70c65b4f67af41ccfd40d21e49880be568997ba6/boto/mturk/question.py
def generate_question_xml(url, frame_height=0):
    schema_url = "http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd"
    template = f'<ExternalQuestion xmlns="{schema_url}"><ExternalURL>{url}</ExternalURL><FrameHeight>{frame_height}</FrameHeight></ExternalQuestion>'
    # lxml etree validate?
    return template


default_qualification = [
    {
        "QualificationTypeId": "00000000000000000071",
        "Comparator": "EqualTo",
        "LocaleValues": [{"Country": "US"}],
    }
]


def generate_hit(*args, **kwargs):
    hit = {
        "Title": "Default String",
        "Description": "Default String",
        "Question": "Default String",
        "Reward": "0.01",
        "AssignmentDurationInSeconds": 86400,
        "LifetimeInSeconds": 86400,
        "Keywords": "expfac",
        "MaxAssignments": 9,
        "AutoApprovalDelayInSeconds": 86400,
        "QualificationRequirements": default_qualification,
    }
    hit.update(kwargs)
    return hit


class BotoWrapper:
    def __init__(self, *args, **kwargs):
        self.client = self.get_client()

    def get_client(self):
        session = boto3.Session()
        return session.client("mturk", endpoint_url=endpoint_url["sandbox"])

    def get_all_hits(self):
        hits = self._consume_paginator("HITs", self.client.list_hits)
        hits_by_url = defaultdict(list)
        for hit in hits:
            re_url = re.search(url_pattern, hit.get("Question", ""))
            if re_url is None:
                continue
            hits_by_url[re_url.group("url")].append(hit)
        return hits_by_url

    def get_active_hits(self):
        hits = self.get_all_hits()
        for url in hits:
            hits[url] = list(
                filter(
                    lambda hit: datetime.now(tzlocal()) < hit["Expiration"], hits[url]
                )
            )
        return hits

    def create_hits_by_url(self, url, num_assignments=9, sandbox=True, *args, **kwargs):
        qxml = generate_question_xml(url)
        hit = generate_hit(Question=qxml, **kwargs)
        try:
            return self.create_hit_batches(hit, num_assignments, sandbox)
        except self.client.exceptions.RequestError as e:
            return e

    def create_hit_batches(self, hit, num_assignments=9, sandbox=True):
        created_hits = []
        for i in range(num_assignments // 9):
            hit["MaxAssignments"] = 9
            created_hits.append(self.client.create_hit(**hit))
        if num_assignments % 9:
            hit["MaxAssignments"] = num_assignments % 9
            created_hits.append(self.client.create_hit(**hit))
        return created_hits

    def expire_hits_by_id(self, ids):
        date = datetime(2015, 1, 1)
        for id in ids:
            self.client.update_expiration_for_hit(HITId=id, ExpireAt=date)
        return

    def expire_hits_by_url(self, url):
        date = datetime(2015, 1, 1)
        hits = self.get_all_hits()
        if url not in hits:
            return
        for hit in hits.get(url, []):
            self.client.update_expiration_for_hit(HITId=hit["HITId"], ExpireAt=date)
        return

    def delete_hits(self, urls):
        hits = self.get_all_hits()
        failed = []
        if urls == "all":
            urls = hits.keys()
        elif type(urls) is str:
            urls = [urls]
        for url in urls:
            for hit in hits[url]:
                try:
                    self.client.delete_hit(HITId=hit["HITId"])
                except self.client.exceptions.RequestError:
                    failed.append(hit)
        return failed

    # list submitted assignments by url
    def list_assignments(self, url=None):
        hits = self.get_all_hits()
        hits_for_url = hits[url]
        assignments = []
        for hit in hits_for_url:
            assignments.extend(
                self._consume_paginator(
                    "Assignments",
                    self.client.list_assignments_for_hit,
                    HITId=hit["HITId"],
                )
            )
        return assignments

    def _consume_paginator(self, key, client_func, max_results=30, **kwargs):
        acc = []
        results = client_func(MaxResults=max_results, **kwargs)
        acc.extend(results.get(key, []))
        next_token = results.get("NextToken", None)
        while next_token:
            results = client_func(
                NextToken=next_token, MaxResults=max_results, **kwargs
            )
            acc.extend(results.get(key, []))
            next_token = results.get("NextToken", None)
        return acc

    def reject_assignments(self, assignment_ids):
        return

    def approve_assignment_by_url(self, url, worker_id):
        return

    def notify_workers(self, subject, message, worker_ids):
        return


"""
qualification_requirements = {
    "QualificationTypeId"
    "Comparator":  LessThan | LessThanOrEqualTo | GreaterThan | GreaterThanOrEqualTo | EqualTo | NotEqualTo | Exists | DoesNotExist | In | NotIn
    "IntegerValues"
    "LocaleValue"
    "ActionsGuarded": Accept | PreviewAndAccept | DiscoverPreviewAndAccept
}
"""
