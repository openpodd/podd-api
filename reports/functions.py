import datetime
import re

import requests
from django.conf import settings

from haystack.query import SearchQuerySet
from haystack.utils.geo import Point

from accounts.models import Authority
from common.functions import (filter_permitted_administration_areas_and_descendants,
    filter_permitted_report_types, filter_permitted_report_types_by_authorities, filter_permitted_administration_areas_and_descendants_by_authorities)
from common.models import get_current_domain_id
from reports.models import Report


def prepare_filter_permitted(allowed_report_type_ids, allowed_administration_area_ids, queryset, params={}):
    # ALWAYS RETURN REPORT TYPE ID 0 (POSITIVE REPORT)
    allowed_report_type_ids = list(allowed_report_type_ids)
    allowed_report_type_ids.append(0)

    if not params.get('administrationArea'):
        queryset = queryset.filter(type__in=allowed_report_type_ids).filter(
            administrationArea__in=allowed_administration_area_ids)
    else:
        if not int(params.get('administrationArea')) in allowed_administration_area_ids:
            queryset = queryset.filter(administrationArea=0)
    return queryset


def _search(q, user, params=None, subscribes=True, current_domain_id=None, allowed_all_reports=False, authority_id=None, tz=0):
    params = params or {}
    queryset = SearchQuerySet().models(Report)

    current_domain_id = current_domain_id or get_current_domain_id(user)
    queryset = queryset.filter(domain=current_domain_id)
    if not allowed_all_reports and not user.is_staff:
        allowed_report_type_ids = filter_permitted_report_types(user, subscribes=subscribes)
        allowed_administration_area_ids = filter_permitted_administration_areas_and_descendants(
            user, subscribes=subscribes, ids_only=True)
        queryset = prepare_filter_permitted(allowed_report_type_ids, allowed_administration_area_ids, queryset, params=params)

    if authority_id:
        allowed_report_type_ids = filter_permitted_report_types_by_authorities(user.domain_id, authority_id, subscribes=subscribes)
        allowed_administration_area_ids = filter_permitted_administration_areas_and_descendants_by_authorities(
            user.domain_id, authority_id, subscribes=subscribes, ids_only=True)
        queryset = prepare_filter_permitted(allowed_report_type_ids, allowed_administration_area_ids, queryset, params=params)

    if q:
        today = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0))
        today = today + datetime.timedelta(hours=-tz)

        tomorrow = today + datetime.timedelta(days=1)
        yesterday = today - datetime.timedelta(days=1)
        week_start = today - datetime.timedelta(days=today.weekday()) - datetime.timedelta(days=1)

        if today - week_start == datetime.timedelta(7):
            week_start = today

        week_end = week_start + datetime.timedelta(days=7)

        q = re.sub('date:[ ]*today', 'date: [%(today)s TO %(tomorrow)s}' % {
            'today': today.strftime('%Y-%m-%dT%H:%M'),
            'tomorrow': tomorrow.strftime('%Y-%m-%dT%H:%M'),
        }, q, flags=re.IGNORECASE)
        q = re.sub('date:[ ]*yesterday', 'date: [%(yesterday)s TO %(today)s}' % {
            'yesterday': yesterday.strftime('%Y-%m-%dT%H:%M'),
            'today': today.strftime('%Y-%m-%dT%H:%M'),
        }, q, flags=re.IGNORECASE)
        q = re.sub('date:[ ]*this week', 'date: [%(week_start)s TO %(week_end)s}' % {
            'week_start': week_start.strftime('%Y-%m-%dT%H:%M'),
            'week_end': week_end.strftime('%Y-%m-%dT%H:%M'),
        }, q, flags=re.IGNORECASE)

        # PATTERN `date: [2015-02-12 TO 2015-02-15]`
        pattern_datetime_range = 'date:[ ]*\[(?P<syear>\d{4})-(?P<smonth>\d{1,2})-(?P<sday>\d{1,2})' \
                                 + '(T(?P<shour>\d{1,2}):(?P<smin>\d{2}))?' \
                                 + ' TO (?P<eyear>\d{4})-(?P<emonth>\d{1,2})-(?P<eday>\d{1,2})' \
                                 +'(T(?P<ehour>\d{1,2}):(?P<emin>\d{2}))?\]'

        pattern = re.compile(pattern_datetime_range, re.IGNORECASE)
        match = pattern.search(q)
        if match and match.groupdict():
            data = match.groupdict()
            try:
                start_day = datetime.datetime(int(data.get('syear')), int(data.get('smonth')), int(data.get('sday')), int(data.get('shour') or 0), int(data.get('smin') or 0))
                end_day = datetime.datetime(int(data.get('eyear')), int(data.get('emonth')), int(data.get('eday')), int(data.get('ehour') or 0), int(data.get('emin') or 0))
            except:
                pass
            else:
                start_day = start_day + datetime.timedelta(hours=-tz)
                end_day = end_day + datetime.timedelta(hours=-tz)

                if data.get('ehour') and data.get('emin'):
                    q = re.sub(pattern_datetime_range, 'date: [%(start_day)s TO %(end_day)s}' % {
                        'start_day': start_day.strftime('%Y-%m-%dT%H:%M'),
                        'end_day': end_day.strftime('%Y-%m-%dT%H:%M'),
                    }, q, flags=re.IGNORECASE)
                else:
                    end_day = end_day + datetime.timedelta(days=1)
                    q = re.sub(pattern_datetime_range, 'date: [%(start_day)s TO %(end_day)s}' % {
                        'start_day': start_day.strftime('%Y-%m-%dT%H:%M'),
                        'end_day': end_day.strftime('%Y-%m-%dT%H:%M'),
                    }, q, flags=re.IGNORECASE)

        # PATTERN `last 7 days`
        pattern_last_x_day = 'date:[ ]*last[ ]*(\d+)[ ]*days'
        pattern = re.compile(pattern_last_x_day, re.IGNORECASE)
        match = pattern.search(q)
        if match and match.groups():
            days = match.group(1)
            last_x_days = today - datetime.timedelta(days=int(days))
            q = re.sub(pattern_last_x_day, 'date: [%(last_x_days)s TO %(today)s}' % {
                'last_x_days': last_x_days.strftime('%Y-%m-%dT%H:%M'),
                'today': tomorrow.strftime('%Y-%m-%dT%H:%M'),
            }, q, flags=re.IGNORECASE)

        queryset = queryset.raw_search(q)

    if params:
        if params.get('authorities'):
            specific_areas = []
            authorities = params.get('authorities')
            for authority_id in authorities:
                authority = Authority.objects.get(id=authority_id)
                specific_areas += [area.id for area in authority.administration_areas.all()]
            queryset = queryset.filter(administrationArea__in=set(specific_areas))
            del params['authorities']

        if params.get('bottom') and params.get('left') and params.get('top') and params.get('right'):

            queryset = queryset.within(
                'reportLocation',
                Point(float(params['top']), float(params['left'])),
                Point(float(params['bottom']), float(params['right']))
            ).order_by('-firstImageThumbnail')
            del (params['bottom'], params['left'], params['top'], params['right'])

    if params.get('order_by'):
        queryset = queryset.order_by(params.get('order_by'))
        del params['order_by']
    else:
        queryset = queryset.order_by('-date')
    queryset = queryset.filter(**params)

    '''
    # SEARCH BY USER
    user = params.pop('user', '')
    if user:
        queryset = queryset.filter(user=user)

    # SEARCH BY REPORT TYPE
    type = params.pop('type', '')
    if type:
        queryset = queryset.filter(type=type)

    # SEARCH BY ADMINISTATION AREA
    administration_area = params.pop('administration_area', '')
    if administration_area:
        queryset = queryset.filter(administration_area=administration_area)

    # SEARCH BY FORM DATA
    if params:
        params_wo_unicode = ast.literal_eval(json.dumps(params))
        params_str = ', '.join("%s: %s" % (key,val) for (key,val) in params_wo_unicode.iteritems())
        queryset = queryset.filter(content=params_str)
    '''

    return queryset


def chat_create_token(report_id, user_id, username):
    """
    :type report_id: int
    :type user_id: int
    :type username: str
    """
    api_url = settings.FIREBASE_CHAT_API_URL + '/createToken?roomId=%d&userId=%d&username=%s'
    headers = {
        'Authorization': 'Secret notebook-door-sky'
    }
    response = requests.post(api_url % (report_id, user_id, username), headers=headers)
    if response.status_code == 200:
        return response.text


def chat_create_room(report_id, room_name, username, welcome_message):
    """
    :type report_id: int
    :type room_name: str
    :type username: str
    :type welcome_message: str
    """
    api_url = settings.FIREBASE_CHAT_API_URL + '/createRoom?roomId=%d&roomName=%s&username=%s&welcomeMessage=%s'
    headers = {
        'Authorization': 'Secret notebook-door-sky'
    }

    response = requests.post(api_url % (report_id, room_name, username, welcome_message), headers=headers)
    if response.status_code == 200:
        return True