from rest_framework import serializers
from experiments import models

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Result
        fields = ['subject', 'data']
