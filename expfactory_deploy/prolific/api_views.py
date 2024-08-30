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

    active_scs = models.StudyCollectionSubject.objects.filter(
        study_collection__active=True,
    )

    ttfs_warned_at = active_scs.filter(
        ttfs_warned_at__isnull=False
    )
    ttcc_warned_at = active_scs.filter(
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
            "status": ss_warn.status,
            "status_reason": ss_warn.status_reason,
        }

    return Response(results)

@api_view(["GET"])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def prolific_kicks(request):
    ss_kicks = models.StudySubject.objects.filter(
        study__study_collection__active=True, status="kicked"
    )

    scs_kicks = models.StudyCollectionSubject.objects.filter(
        study_collection__active=True, status="kicked"
    )

    results = defaultdict(lambda: defaultdict(dict))
    for scs in scs_kicks:
        results[scs.study_collection.id][scs.subject.prolific_id] = {
            "status": scs.status,
            "status_reason": scs.status_reason,
            "failed_at": scs.failed_at,
        }
    for ss in ss_kicks:
        results[ss.study.study_collection.id][ss.subject.prolific_id][
            ss.study.remote_id
        ] = {
            "battery": ss.study.battery.title,
            "study_rank": ss.study.rank,
            "status": ss.status,
            "status_reason": ss.status_reason,
            "failed_at": ss.failed_at,
        }
    return Response(results)

@api_view(["GET"])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def prolific_suspensions(request):
    scs_suspended = models.StudyCollectionSubject.objects.filter(
        study_collection__active=True, active=False
    )
    results = []
    for scs in scs_suspended:
        results.append({
            'study_collection_id': scs.study_collection.id,
            'subject_id': scs.subject.prolific_id,
            'status': scs.status,
            'status_reason': scs.status_reason,
        })
    return Response(results)


