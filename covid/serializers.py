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

    class Meta:
        model = MonitoringReport
        fields = (
            'id', 'name', 'started_at', 'until', 'report_id', 'authority_id', 'status', 'report', 'followup_count',
            'latest_followup_date')


class DailySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySummary


class DailySummaryByVillageSerializer(serializers.ModelSerializer):
    class Meta:
        mode = DailySummaryByVillage
