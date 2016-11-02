from rest_framework import serializers

from accounts.serializers import UserSerializer
from mentions.models import Mention

class MentionSerializer(serializers.ModelSerializer):
    createdAt = serializers.WritableField('created_at', read_only=True)
    isNotified = serializers.WritableField('is_notified')
    reportId = serializers.Field(source='comment.report.id')
    seenAt = serializers.WritableField('seen_at')

    class Meta:
        model = Mention
        fields = ('id', 'reportId', 'mentionee', 'mentioner', 'isNotified', 'createdAt', 'seenAt')

    def transform_mentionee(self, obj, value):
        if obj and obj.id:
            return UserSerializer(obj.mentionee).data
        return ''

    def transform_mentioner(self, obj, value):
        if obj and obj.id:
            return UserSerializer(obj.mentioner).data
        return ''

    def transform_createdAt(self, obj, value):
        if value:
            return value.isoformat()
        return value

    def transform_seenAt(self, obj, value):
        if value:
            return value.isoformat()
        return value