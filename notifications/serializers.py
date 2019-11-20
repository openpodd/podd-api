
import json
import re
from django.forms import widgets

from rest_framework import serializers
from accounts.serializers import AttachCanEditSerializer, UserSerializer

from notifications.models import Notification, NotificationTemplate, NotificationAuthority
from reports.models import ReportType
from reports.serializers import ReportSerializer


class NotificationTemplateSerializer(serializers.ModelSerializer, AttachCanEditSerializer):

    class Meta:
        model = NotificationTemplate
        fields = ('id', 'type', 'template', 'condition', 'description', 'authority')


class AuthorityNotificationTemplateSerializer(serializers.ModelSerializer, AttachCanEditSerializer):

    enabled = serializers.SerializerMethodField('get_enabled')
    can_disable = serializers.SerializerMethodField('get_can_disable')

    class Meta:
        model = NotificationTemplate
        fields = ('id', 'type', 'template', 'condition', 'description', 'authority', 'enabled', 'can_disable')

    def get_enabled(self, obj):
        return obj.enabled(self.context['parent'])

    def get_disabled(self, obj):
        return obj.disabled(self.context['parent'])

    def get_can_disable(self, obj):
        return obj.can_disable(self.context['parent'])


class NotificationAuthoritySerializer(serializers.ModelSerializer):

    template = serializers.PrimaryKeyRelatedField('template', widget=widgets.TextInput)
    authority = serializers.PrimaryKeyRelatedField('authority', widget=widgets.TextInput)
    to = serializers.WritableField('to', required=False)

    class Meta:
        model = NotificationAuthority
        fields = ('id', 'template', 'authority', 'to')


class AuthorityNotificationTemplateFullSerializer(AuthorityNotificationTemplateSerializer):

    contact = serializers.SerializerMethodField('get_contact')
    typeName = serializers.SerializerMethodField('get_type_name')

    class Meta:
        model = NotificationTemplate
        fields = ('id', 'type', 'template', 'condition', 'typeName', 'description', 'authority', 'contact', 'enabled', 'can_disable')

    def get_contact(self, obj):
        if obj and obj.id:
            try:
                authority = self.context['parent']
                notification_authority = NotificationAuthority.objects.get(template=obj, authority=authority)
                return NotificationAuthoritySerializer(notification_authority).data
            except NotificationAuthority.DoesNotExist:
                pass
        return ''

    def get_type_name(self, obj):

        if obj and obj.description:
            try:
                return obj.description.split(':')[1].strip()
            except IndexError:
                pass

        return ''





class NotificationSerializer(serializers.ModelSerializer):
    receiveUser = serializers.PrimaryKeyRelatedField(source='receive_user', required=False, read_only=True)
    to = serializers.Field(source='to')
    refNo = serializers.Field(source='ref_no')
    reportFirstThumbnailUrl = serializers.Field(source='get_first_image_thumbnail_url')
    reportTypeName = serializers.Field(source='report.type.name')
    seenAt = serializers.Field(source='seen_at')

    notificationAuthority = serializers.PrimaryKeyRelatedField('notification_authority', required=False, read_only=True, widget=widgets.TextInput)


    createdBy = UserSerializer(source='created_by', read_only=True)
    createdAt = serializers.WritableField('created_at', read_only=True)
    renderWebMessage = serializers.Field('render_web_message')

    class Meta:
        model = Notification
        fields = ('id', 'report', 'to', 'refNo', 'receiveUser', 'type', 'createdAt', 'createdBy', 'reportTypeName', 'reportFirstThumbnailUrl', 'renderWebMessage', 'message', 'seenAt')
