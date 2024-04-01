import ast
import json

from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from experiments import models

def get_result(pk):
    result = get_object_or_404(models.Result, id=pk)
    data = ast.literal_eval(result.data)
    return JsonResponse({'data': data, 'subject': result.subject.id})

filter_lookup = {
    'subject_id': 'subject_id',
    'battery_id': 'assignment__battery_id',
    'sc_id': 'assignment__battery__study__study_collection__id'
}

def get_results(**kwargs):
    filter_kwargs = {}
    for k, v in kwargs.items():
        filter_k = filter_lookup.get(k, None)
        if filter_k is None or v is None:
            continue
        filter_kwargs[filter_k] = v
    results = models.Result.objects.filter(**filter_kwargs)
    results = results.values('id', 'data').annotate(
        study_collection_id=F("assignment__battery__study__study_collection__id"),
        study_collection_name=F("assignment__battery__study__study_collection__name"),
        battery_name=F("assignment__battery__title"),
        battery_id=F("assignment__battery__id"),
        exp_name=F("battery_experiment__experiment_instance__experiment_repo_id__name"),
        prolific_id=F("assignment__subject__prolific_id"),
    )
    return results


'''
    This is currently done with the above annotations on the query set. Not sure which is more performant.

def result_format(result):
    return result
    started_at = None if result.started_at is None else result.started_at.isoformat()
    completed_at = None if result.completed_at is None else result.completed_at.isoformat()
    result = {
        'battery_id': result.assignment.battery_id,
        'subject_id': result.subject.prolific_id,
        'exp_id': result.battery_experiment.id,
        'exp_name': result.battery_experiment.experiment_instance.experiment_repo_id.name,
        'started_at': started_at,
        'completed_at': completed_at,
        'data': ast.literal_eval(result.data)
    }

def get_and_format(**kwargs):
    results = get_results(**kwargs)
    return [result_format(x) for x in results]
'''

class ResultSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return instance

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_results_view(request, **kwargs):
    paginator = LimitOffsetPagination()
    # paginator.default_limit = 1

    # why dont we just pass **Request.GET to get_results?
    query_args = {
        'subject_id': request.GET.get('subject_id'),
        'battery_id': request.GET.get('battery_id'),
        'sc_id': request.GET.get('sc_id'),
    }
    results = get_results(**query_args)
    result_page = paginator.paginate_queryset(results, request)
    serializer = ResultSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)
