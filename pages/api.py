# -*- encoding: utf-8 -*-

import datetime
import json

from django.db.models import Count, Q
from django.http import HttpResponse
from django_redis import get_redis_connection
from dateutil.relativedelta import relativedelta

from rest_framework import viewsets, status, filters
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, action, authentication_classes, link, permission_classes, list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from accounts.models import GroupReportType, User, Configuration, Authority
from accounts.serializers import UserCommonShortDetailSerializer

from common.constants import USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER
from common.functions import filter_permitted_users_by_authorities
from logs.models import LogItem

from notifications.models import NotificationTemplate
from notifications.serializers import AuthorityNotificationTemplateFullSerializer

from reports.api import _view_administration_area_contacts
from reports.functions import _search
from reports.serializers import PositiveReportListESSerializer

from pages import Authority as AuthorityDetail
from summary.api import _daily_summary_performance_user, _summary_dashboard_visualization, _summary_report_visualization


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def dashboard(request):

    if request.QUERY_PARAMS.get('authorityId'):
        try:
            authority = Authority.objects.get(id=request.QUERY_PARAMS.get('authorityId'))
        except Authority.DoesNotExist:
            return Response({"authorityId": "Invalid authorityId. authorityId does not exist."},
                status=status.HTTP_400_BAD_REQUEST)
    else:
        if request.user.is_staff:
            authority = None
        else:
            authority = request.user.get_my_authority()

    force = False
    if request.QUERY_PARAMS.get('force'):
        force = request.QUERY_PARAMS.get('force')

    today = request.QUERY_PARAMS.get('date')
    try:
        today = datetime.datetime.strptime(today, '%d/%m/%Y')
    except:
        today = datetime.datetime.now()

    r = get_redis_connection()

    search = 'cache-dashboard-authority[%(authority)s]' % {
           'day': today.day, 'month': today.month, 'year': today.year, 'authority': authority.id if authority else '-',
    }

    value = r.get(search)
    if value and not force:
        return HttpResponse(value, content_type="application/json")
    else:

        if request.QUERY_PARAMS.get('tz'):
            offset_timezone = int(request.QUERY_PARAMS.get('tz'))
        else:
            offset_timezone = 0

        page_size = 3
        if request.QUERY_PARAMS.get('page_size'):
            page_size = int(request.QUERY_PARAMS.get('page_size'))
        else:
            page_size = 3

        subscribes = request.QUERY_PARAMS.get('subscribe') == 'true'

        result = AuthorityDetail(id=(authority.id if authority else None), name=(authority.name if authority else None))
        result.visualization = _summary_dashboard_visualization(request, authority_id=(authority.id if authority else None))
        result.reportThisWeek = _summary_report_visualization(request, authority_id=(authority.id if authority else None))

        q = 'type:0 AND date:[ * TO ' + today.strftime('%Y-%m-%d') + ']'
        positive_reports = _search(q, request.user, params={'order_by': '-date'},
                                   subscribes=subscribes,
                                   authority_id=(authority.id if authority else None), tz=offset_timezone)[:page_size]
        result.positiveReports = PositiveReportListESSerializer(positive_reports, many=True).data

        roles_string = '"%s","%s"' % (USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER)
        if not request.user.is_staff:
            user_ids = filter_permitted_users_by_authorities(request.user.domain_id, authority.id, subscribes=subscribes, status=roles_string)[:page_size]
            users = User.objects.filter(id__in=user_ids)
        else:
            users = User.objects.order_by('-date_joined')[:page_size]
        result.newlyReporters = UserCommonShortDetailSerializer(users, many=True).data

        result.performanceReporters = _daily_summary_performance_user(request, authority_id=(authority.id if authority else None))
        result.contacts = _view_administration_area_contacts(request, authority_id=(authority.id if authority else None), is_paginator=False)

        if authority:
            result.notificationTemplates = AuthorityNotificationTemplateFullSerializer(authority.notification_template_enabled_list(), many=True, context={'parent': authority}).data
        else:
            result.notificationTemplates = AuthorityNotificationTemplateFullSerializer(NotificationTemplate.objects.all()[:page_size], many=True, context={'parent': authority}).data

        key = 'cache-dashboard-authority[%(authority)s]' % {
           'day': today.day, 'month': today.month, 'year': today.year, 'authority': (authority.id if authority else '-'),
        }
        r.set(key, json.dumps(result, default=lambda o: o.__dict__))

    value = r.get(search)
    if value:
        return HttpResponse(value, content_type="application/json")


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def log_dashboard_view(request):

    # find default authority
    admin_area = request.user.administration_area
    if admin_area:
        user_authority = admin_area.authority
    elif request.user.authority_users.count() > 0:
        user_authority = request.user.authority_users.all()[0]
    else:
        return HttpResponse('{"detail":"ignored"}', content_type="application/json")

    if not request.QUERY_PARAMS.get('path'):
        return HttpResponse('{"detail":"ignored"}', content_type="application/json")

    # insert log action
    LogItem.objects.log_action(
        key='DASHBOARD_VIEW',
        created_by=request.user,
        object1=user_authority,
        data={
            'path': request.QUERY_PARAMS.get('path')
        }
    )

    return HttpResponse('{"detail":"ok"}', content_type="application/json")