from rest_framework import serializers
from common.models import Domain


class DomainSerializer(serializers.ModelSerializer):
    id = serializers.Field('pk')
    name = serializers.Field('name')

    class Meta:
        model = Domain
        fields = ('id', 'name')