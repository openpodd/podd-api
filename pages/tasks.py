# -*- encoding: utf-8 -*-


import datetime
import json

from django_redis import get_redis_connection

from accounts.models import GroupReportType, User, Configuration, Authority
from accounts.serializers import UserCommonShortDetailSerializer

from common.constants import USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER
from common.functions import filter_permitted_users_by_authorities, filter_permitted_administration_areas_and_descendants_by_authorities

from notifications.serializers import AuthorityNotificationTemplateFullSerializer

from reports.api import _view_administration_area_contacts
from reports.functions import _search
from reports.serializers import PositiveReportListESSerializer

from pages import Authority as AuthorityDetail
from summary.api import _daily_summary_performance_user, _summary_dashboard_visualization, _summary_report_visualization

from podd.celery import app


class QueryParams:
    q = {}

    def get(self, key):
        return self.q.get(key)

    def getlist(self, key):
        return self.get(key)


class Request:
    QUERY_PARAMS = QueryParams()

    def __init__(self, user=None):
        if not user:
            self.user = User.objects.get(username='system')
        self.user = user

    def getlist(self):
        return None


@app.task
def fetch_dashboard_for_every_days(subscribes=False, offset_timezone=7, page_size=3):
    today = datetime.datetime.now()
    r = get_redis_connection()

    index = 1
    for authority in Authority.objects.all():
        authority_user_list = authority.users.all()
        if len(authority_user_list) == 0:
            continue

        request = Request(user=authority_user_list[0])
        request.QUERY_PARAMS = QueryParams()
        request.QUERY_PARAMS.q = {
            'month': today.strftime('%m/%Y'),
            'lastWeek': True,
            'name__startsWith': u'บ้าน',
            'page_size': page_size,
            'subscribes': False,
            'tz': offset_timezone
        }

        print index, '', authority
        index += 1

        # research team doesn't have its own areas, need to subscribe areas only !!, so cannot use this function!!
        if authority.code == 'researcher-cnx':
            continue

        # cannot search because domain...
        if authority.domain_id != 1:
            continue

        # because they can see the reports from subscribe areas, no own areas...
        administration_areas = len(filter_permitted_administration_areas_and_descendants_by_authorities(authority.domain_id, authority.id, ids_only=True))
        if administration_areas == 0:
            continue

        result = AuthorityDetail(id=(authority.id if authority else None), name=(authority.name if authority else None))
        result.visualization = _summary_dashboard_visualization(request, current_domain_id=(authority.domain_id if authority else None), authority_id=(authority.id if authority else None))
        result.reportThisWeek = _summary_report_visualization(request, current_domain_id=(authority.domain_id), authority_id=(authority.id if authority else None))

        q = 'type:0 AND date:[ * TO ' + today.strftime('%Y-%m-%d') + ']'
        positive_reports = _search(q, request.user, params={'order_by': '-date'},
                                   current_domain_id=(authority.domain_id if authority else None),
                                   subscribes=subscribes,
                                   authority_id=(authority.id if authority else None), tz=offset_timezone)[:page_size]
        result.positiveReports = PositiveReportListESSerializer(positive_reports, many=True).data

        roles_string = '"%s","%s"' % (USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER)
        user_ids = filter_permitted_users_by_authorities(authority.domain_id, authority.id, subscribes=subscribes, status=roles_string)[:page_size]
        users = User.objects.filter(id__in=user_ids)
        result.newlyReporters = UserCommonShortDetailSerializer(users, many=True).data

        result.performanceReporters = _daily_summary_performance_user(request, authority_id=(authority.id if authority else None))
        result.contacts = _view_administration_area_contacts(request, authority_id=(authority.id if authority else None), is_paginator=False)

        result.notificationTemplates = AuthorityNotificationTemplateFullSerializer(authority.notification_template_enabled_list(), many=True, context={'parent': authority}).data

        key = 'cache-dashboard-authority[%(authority)s]' % {
           'day': today.day, 'month': today.month, 'year': today.year, 'authority': (authority.id if authority else '-'),
        }
        r.set(key, json.dumps(result, default=lambda o: o.__dict__))

