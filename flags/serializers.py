from rest_framework import serializers

from flags.models import Flag

class FlagSerializer(serializers.ModelSerializer):
    createdAt = serializers.WritableField('created_at', read_only=True)
    flagOwner = serializers.WritableField('flag_owner', read_only=True)
    reportNegative = serializers.SerializerMethodField('get_report_negative')
    reportId = serializers.Field(source='comment.report.id')

    class Meta:
        model = Flag
        fields = ('id', 'reportId', 'priority', 'flagOwner', 'createdAt', 'reportNegative')

    def transform_flagOwner(self, obj, value):
        if obj and obj.id:
            return obj.flag_owner.username
        return ''

    def transform_createdAt(self, obj, value):
        if value:
            return value.isoformat()
        return value

    def get_report_negative(self, obj):
        if obj:
            return obj.comment.report.negative
        return True
