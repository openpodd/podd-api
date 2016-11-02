
from rest_framework import serializers


class ReportSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=200)
    data = serializers.IntegerField()
