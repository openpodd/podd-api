from rest_framework import serializers

from monitorings.models import Monitoring

class MonitorSerializer(serializers.ModelSerializer):
    createdAt = serializers.WritableField('created_at', read_only=True)

    class Meta:
        model = Monitoring
        fields = ('id', 'uploadedfile', 'createdAt')

    def transform_createdAt(self, obj, value):
        if value:
            return value.isoformat()
        return value