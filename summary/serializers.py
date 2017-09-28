import json

from rest_framework import serializers

from summary.models import AggregateReport


class ReportSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=200)
    data = serializers.IntegerField()


class AggregateReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=500)
    filter_definition = serializers.CharField()

    class META:
        model = AggregateReport
        fields = ('id', 'name', 'filter_definition')

    def transform_data_defintion(self, obj, value):
        if value:
            return json.loads(value)
        return value