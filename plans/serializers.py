import json
from django.forms import widgets

from rest_framework import serializers
from plans.functions import plan_user_get_level_areas
from plans.models import Plan, PlanReport, PlanLevel


class PlanLevelSerializer(serializers.ModelSerializer):

    extraData = serializers.WritableField('extra_data', read_only=True)

    class Meta:
        model = PlanLevel
        fields = ('id', 'name', 'code', 'distance', 'extraData')

    def transform_extraData(self, obj, value):
        return json.loads(value or '{}')


class PlanSerializer(serializers.ModelSerializer):

    levels = PlanLevelSerializer(many=True, read_only=True)


    class Meta:
        model = Plan
        fields = ('id', 'name', 'code', 'condition', 'levels')


class PlanReportSerializer(serializers.ModelSerializer):

    report = serializers.PrimaryKeyRelatedField('report', read_only=True, widget=widgets.TextInput)
    createdAt = serializers.WritableField('created_at', read_only=True)
    log = serializers.WritableField('log', read_only=True)
    reportTypeName = serializers.Field('report.type.name')

    reportStateCode = serializers.Field('report.state.code')
    reportStateName = serializers.Field('report.state.name')

    incidentArea = serializers.Field('report.administration_area.address')

    class Meta:
        model = PlanReport
        fields = ('id', 'plan', 'report', 'log', 'createdAt',
                  'reportTypeName', 'reportStateCode', 'reportStateName', 'incidentArea')


    def transform_log(self, obj, value):

        log = json.loads(value or '{}')
        request = self.context['request']

        if log.get('level_areas'):
            log['my_level_areas'] = plan_user_get_level_areas(request.user, log.get('level_areas'))

        if log.get('report') and not request.GET.get('displayLogReport'):
            del(log['report'])


        return log

