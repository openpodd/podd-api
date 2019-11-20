import json

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone

from rest_framework import status, viewsets, filters
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, detail_route, action, link, \
    list_route
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from accounts.models import Authority
from common.api import ParentModelMixin

from notifications import tasks
from notifications.functions import import_notification_excel
from notifications.models import Notification, NotificationTemplate, NotificationAuthority
from notifications.serializers import NotificationSerializer, NotificationTemplateSerializer, \
    NotificationAuthoritySerializer, AuthorityNotificationTemplateSerializer, AuthorityNotificationTemplateFullSerializer


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def seen_notification(request):
    '''
    *params*
    {
        'notificationId': '123',         
    }
    '''
    notification_id = request.DATA.get('notificationId')
    if notification_id:
        notification = Notification.objects.get(pk=notification_id)
        notification.seen_at = timezone.now()
        notification.save()
    return Response({}, status=status.HTTP_200_OK)


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return NotificationTemplate.objects.all()


class NotificationAuthorityViewSet(viewsets.ModelViewSet):
    model = NotificationAuthority
    serializer_class = NotificationAuthoritySerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('authority', 'template',)

    def get_queryset(self):
        return NotificationAuthority.objects.all()


class AuthorityNotificationTemplateViewSet(viewsets.ModelViewSet, ParentModelMixin):
    model = NotificationTemplate
    serializer_class = AuthorityNotificationTemplateSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    parent_model = Authority

    def get_queryset(self):

        self.kwargs['parent'] = Authority.objects.get(id=self.kwargs['parent_pk']) # for single query
        authority = self.kwargs['parent']
        status = self.kwargs.get('status')

        query = authority._base_notification_template_list

        if status:
            if status == 'enabled':
                query = authority.notification_template_enabled_list()
            elif status == 'disabled':
                query = authority.notification_template_disabled_list()
            elif status == 'cannotDisable':
                query = authority.notification_template_cannot_disable_list()

        return query

    def list(self, request, *args, **kwargs):
        kwargs['parent'] = Authority.objects.get(id=self.kwargs['parent_pk']) # for single query
        queryset = self.get_queryset().order_by('id')

        if request.QUERY_PARAMS.get('full'):
            serializer = AuthorityNotificationTemplateFullSerializer(queryset, many=True, context=kwargs)
        else:
            serializer = AuthorityNotificationTemplateSerializer(queryset, many=True, context=kwargs)
        return Response(serializer.data)

    @action()
    def enable(self, request, pk, *args, **kwargs):

        # print request.DATA.get('to')

        self.kwargs['parent'] = Authority.objects.get(id=self.kwargs['parent_pk']) # for single query
        authority = self.kwargs['parent']

        self.object = NotificationTemplate.objects.get(id=pk)

        self.object.enable(authority, request.DATA.get('to', ''))

        serializer = self.get_serializer(self.object)
        return Response(serializer.data)


    @action()
    def disable(self, request, pk, *args, **kwargs):

        self.kwargs['parent'] = Authority.objects.get(id=self.kwargs['parent_pk']) # for single query
        authority = self.kwargs['parent']

        self.object = self.get_object()
        self.object.disable(authority)

        serializer = self.get_serializer(self.object)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    model = Notification
    serializer_class = NotificationSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100


    def get_queryset(self):
        only_self = self.request.QUERY_PARAMS.get('onlySelf', True)
        if only_self == 'no':
            queryset = Notification.objects.filter()
        else:
            queryset = Notification.objects.filter(receive_user=self.request.user)

        ref_no = self.request.QUERY_PARAMS.get('ref_no', None)
        if ref_no:
            queryset = queryset.filter(ref_no=ref_no)

        createdAt__gt = self.request.QUERY_PARAMS.get('createdAt__gt', None)
        if createdAt__gt is not None:
            queryset = queryset.filter(created_at__gt=createdAt__gt)

        createdAt__lt = self.request.QUERY_PARAMS.get('createdAt__lt', None)
        if createdAt__lt is not None:
            queryset = queryset.filter(created_at__lt=createdAt__lt)

        report_id = self.request.QUERY_PARAMS.get('report__id', None)
        if report_id:
            queryset = queryset.filter(report__id=report_id)

        return queryset

    def list(self, request, *args, **kwargs):

        result = super(NotificationViewSet, self).list(request, *args, **kwargs)
        self.get_queryset().update(is_seen=True)

        return result

    def retrieve(self, request, *args, **kwargs):

        result = super(NotificationViewSet, self).retrieve(request, *args, **kwargs)

        self.object.seen_at = timezone.now()
        self.object.save()

        return result

    @list_route()
    def unseen(self, request):
        return Response({'count': self.get_queryset().filter(is_seen=False).count()})


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def import_notifications(request):
    success = None
    if request.method == 'POST':
        file = request.FILES.get('file')
        template_id = request.POST.get('template')

        if file and template_id:
            success = import_notification_excel(template_id, file)

    return Response(success)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def test_send_notifications(request):
    data = request.DATA

    users = data.get('users')

    message = data.get('message')

    if not users:
        return Response({"users": "users is required."},
                        status=status.HTTP_400_BAD_REQUEST)

    if not message:
        return Response({"message": "message is required."},
                        status=status.HTTP_400_BAD_REQUEST)

    message_type = data.get('type')
    subject = data.get('message')
    if subject:
        subject = subject[0:30] if len(subject) > 30 else subject

    if message_type:
        if message_type == Notification.SMS_ONLY:
            tasks.test_send_notification.delay(Notification.SMS_ONLY, users, subject=subject, message=message)

        elif message_type == Notification.EMAIL_ONLY:
            tasks.test_send_notification.delay(Notification.EMAIL_ONLY, users, subject=subject, message=message)

    else:
        tasks.test_send_notification.delay(Notification.SMS_ONLY, users, subject=subject, message=message)
        tasks.test_send_notification.delay(Notification.EMAIL_ONLY, users, subject=subject, message=message)

    return Response({})
