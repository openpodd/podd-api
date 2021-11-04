from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from covid.models import MonitoringReport, DailySummaryByVillage, DailySummary


class MonitoringReportSerializer(serializers.ModelSerializer):
    report = serializers.SlugRelatedField(
        read_only=True,
        many=False,
        slug_field="guid"
    )
    report_id = serializers.PrimaryKeyRelatedField(many=False, read_only=True, source="report")
    authority_id = serializers.PrimaryKeyRelatedField(many=False, read_only=True, source="authority")
    status = serializers.WritableField(source="report_latest_state_code")
    tag = serializers.CharField(read_only=True)
    tag = serializers.SerializerMethodField('get_tag')

    class Meta:
        model = MonitoringReport
        fields = (
            'id', 'name', 'started_at', 'until', 'report_id', 'authority_id', 'status', 'report', 'followup_count',
            'latest_followup_date', 'tag')

    def get_tag(self, report):
        now = timezone.now().date()
        if not report.latest_followup_date:
            return None
        duration = now - report.latest_followup_date
        if duration.days > settings.COVID_FOLLOWUP_NOTIFICATION_ALARM_DAYS:
            return settings.COVID_FOLLOWUP_TAG % (settings.COVID_FOLLOWUP_NOTIFICATION_ALARM_DAYS,)


class DailySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySummary


class DailySummaryByVillageSerializer(serializers.ModelSerializer):
    class Meta:
        mode = DailySummaryByVillage
