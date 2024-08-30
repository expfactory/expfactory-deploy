from collections import defaultdict

from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from prolific import models

@api_view(["GET"])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def prolific_warnings(request):
    ss_warnings = models.StudySubject.objects.filter(
        study__study_collection__active=True, warned_at__isnull=False
    )

    ttfs_warned_at = models.StudyCollectionSubject.objects.filter(
        ttfs_warned_at__isnull=False
    )
    ttcc_warned_at = models.StudyCollectionSubject.objects.filter(
        ttcc_warned_at__isnull=False
    )
    scs_warnings = ttfs_warned_at | ttcc_warned_at

    results = defaultdict(lambda: defaultdict(dict))
    for scs_warn in scs_warnings:
        entry = {}
        if scs_warn.ttfs_warned_at:
            entry["ttfs_warned_at"] = scs_warn.ttfs_warned_at
        if scs_warn.ttcc_warned_at:
            entry["ttcc_warned_at"] = scs_warn.ttcc_warned_at
        results[scs_warn.study_collection.name][scs_warn.subject.prolific_id] = entry

    for ss_warn in ss_warnings:
        results[ss_warn.study.study_collection.name][ss_warn.subject.prolific_id][
            ss_warn.study.remote_id
        ] = {
            "battery": ss_warn.study.battery.title,
            "study_rank": ss_warn.study.rank,
            "warned_at": ss_warn.warned_at,
            "current_status": ss_warn.status,
            "status_reason": ss_warn.status_reason,
        }

    return Response(results)
