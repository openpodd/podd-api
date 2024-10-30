# -*- encoding: utf-8 -*-

import collections
import datetime
import json
import operator
import random
import string

import os
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Count, Q
from django.http import HttpResponse, Http404
from django.db import connection
from future.utils import iteritems
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Configuration, User, Authority
from accounts.serializers import AuthorityListSerializer
from common.constants import USER_STATUS_CAREGIVER, USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER
from common.functions import (filter_permitted_administration_areas_and_descendants,
                              get_administration_area_and_descendants, multi_level_dict_to_one_level_dict,
                              filter_permitted_report_types,
                              filter_permitted_users, filter_permitted_users_by_authorities,
                              filter_permitted_report_types_by_authorities,
                              filter_permitted_authority, filter_permitted_authority_by_authorities)
from common.podd_elasticsearch import get_elasticsearch_instance
from reports.functions import _search
from reports.models import Report, AdministrationArea, ReportType
from reports.serializers import ReportListESSerializer, AdministrationAreaListSerializer
from summary.functions import get_elastic_search_body
from summary.models import AggregateReport, SummaryReport
from summary.objects import (AreaDate, AreaDetail,
                             ReporterDetail, ReportTypeTemplate, MonthlyReporter)
from summary.serializers import ReportSummarySerializer, AggregateReportSerializer
from sendfile import sendfile



class AggregateReportViewSet(viewsets.ModelViewSet):
    model = AggregateReport
    serializer_class = AggregateReportSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    # @cache_response(60 * 5)
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        serializer = AggregateReportSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def run_aggregate_report(request, id):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    date_start = body['dateStart']
    date_end = body['dateEnd']
    ids = filter_permitted_authority(request.user)

    file_name = ''.join([random.choice(string.ascii_lowercase) for i in range(16)]) + '.xls'
    path = settings.SENDFILE_ROOT
    output = os.path.join(path, file_name)
    report = AggregateReport.objects.get(pk=id)
    m = __import__(report.module)
    params = {
        'domain_id': request.user.domain_id,
        'date_begin': date_start,
        'date_end': date_end,
        'authority_ids': ids,
    }
    success = m.process.run(params, connection, output)

    return HttpResponse(json.dumps({
        'success': success,
        'url': '/summary/aggregateReport/result/%s/' % (file_name,)
    }), content_type="application/json")


@api_view(['GET'])
def serve_aggregate_report(request, name):
    path = settings.SENDFILE_ROOT
    output = os.path.join(path, name)
    return sendfile(request, output)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def monthly_summary(request):
    user = request.user
    results = []
    mapAuthority = {}
    for report in SummaryReport.objects.filter(authority__in=(Authority.objects.filter(users=user))).order_by('authority__name', '-year', '-month'):
        authority_id = report.authority.id
        authority_name = report.authority.name

        auth = None
        if report.authority.id not in mapAuthority:
            auth = {
                'name': authority_name,
                'id': authority_id,
                'reports': []
            }
            mapAuthority[authority_id] = auth
            results.append(auth)

        else:
            auth = mapAuthority[authority_id]

        auth['reports'].append({
            'year': report.year,
            'month': report.month,
            'url': report.url,
        })

    return HttpResponse(json.dumps(results), content_type="application/json")


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def summary_by_number_of_report(request):
    dates = request.QUERY_PARAMS.get('dates')
    try:
        date_range = dates.split('-')
        date_start = datetime.datetime.strptime(date_range[0], "%d/%m/%Y")
        date_end = datetime.datetime.strptime(date_range[1], "%d/%m/%Y")
        if request.QUERY_PARAMS.get('tz'):
            offset_timezone = int(request.QUERY_PARAMS.get('tz'))
        else:
            offset_timezone = 0
    except:
        return Response({"dates": "Invalid dates. Please try again. (eg. 12/01/2015-18/01/2015)"},
                        status=status.HTTP_400_BAD_REQUEST)
    else:
        results = []

        dates = []
        delta = date_end - date_start
        for i in range(delta.days + 1):
            date = date_start + datetime.timedelta(days=i)
            dates.append(date)

        administration_areas = {}

        if request.user.is_staff:
            user_areas = AdministrationArea.objects.all()
        else:
            user_areas = filter_permitted_administration_areas_and_descendants(request.user)

        areas = [user_area for user_area in user_areas if user_area.is_leaf()]
        areas_ids = []

        for area in areas:
            if area.get_parent():
                try:
                    parent_name = area.get_parent().name
                except:
                    parent_name = ''
            else:
                parent_name = ''
            administration_areas[area.id] = AreaDate(id=area.id, name=area.name, parent_name=parent_name,
                                                     address=area.address, location=area.location.json, dates=dates)
            areas_ids.append(area.id)

        reports = Report.objects.filter(administration_area__in=areas).filter(
            date__gte=date_start + datetime.timedelta(hours=-offset_timezone),
            date__lt=date_end + datetime.timedelta(days=1, hours=-offset_timezone)
        ).exclude(test_flag=True).values('date', 'negative', 'created_by', 'administration_area')

        for report in reports:
            try:
                report_date = (report['date'] + datetime.timedelta(hours=offset_timezone)).strftime('%d-%m-%Y')
                administration_areas[report['administration_area']].put_report(report_negative=report['negative'],
                                                                               report_date=report_date)
            except KeyError:
                pass

        for key, administration_area in iteritems(administration_areas):
            results.append(administration_area)

        return HttpResponse(json.dumps(results, default=lambda o: o.__dict__), content_type="application/json")


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def summary_by_inactive_person(request):
    dates = request.QUERY_PARAMS.get('dates')
    try:
        date_range = dates.split('-')
        date_start = datetime.datetime.strptime(date_range[0], "%d/%m/%Y")
        date_end = datetime.datetime.strptime(date_range[1], "%d/%m/%Y")
        if request.QUERY_PARAMS.get('tz'):
            offset_timezone = int(request.QUERY_PARAMS.get('tz'))
        else:
            offset_timezone = 0
    except:
        return Response({"dates": "Invalid dates. Please try again. (eg. 12/01/2015-18/01/2015)"},
                        status=status.HTTP_400_BAD_REQUEST)
    else:
        results = []

        date_count = (date_end - date_start).days + 1

        if request.QUERY_PARAMS.get('percent'):
            percent_threshold = int(request.QUERY_PARAMS.get('percent'))
        else:
            try:
                percent_threshold = int(
                    Configuration.objects.get(system='web.summary.minimum_reports', key='percent').value)
            except:
                percent_threshold = 10

        threshold_report = float(percent_threshold * date_count) / 100

        if request.user.is_staff:
            user_areas = AdministrationArea.objects.all()
        else:
            user_areas = filter_permitted_administration_areas_and_descendants(request.user)

        report_users = Report.objects.filter(administration_area__in=user_areas).filter(
            date__gte=date_start + datetime.timedelta(hours=-offset_timezone),
            date__lt=date_end + datetime.timedelta(days=1, hours=-offset_timezone)
        ).exclude(test_flag=True).values('created_by').annotate(Count('created_by')).order_by('-created_by__count')

        user_ids = []
        for report_user in report_users:
            if report_user['created_by__count'] >= threshold_report:
                user_ids.append(report_user['created_by'])

        users = User.objects.filter(status=USER_STATUS_VOLUNTEER)
        if not request.user.is_staff:
            user_authority_ids = filter_permitted_users(request.user)
            users = users.filter(id__in=user_authority_ids)
        users = users.exclude(id__in=user_ids)

        for user in users:
            if user.administration_area and user.administration_area.get_parent():
                parent_administration_area = user.administration_area.get_parent().name
            else:
                parent_administration_area = ''

            if user.administration_area:
                administration_area = user.administration_area.name
            else:
                administration_area = ''

            try:
                total_report = report_users.get(created_by=user)['created_by__count']
            except (Report.DoesNotExist, KeyError):
                total_report = 0

            results.append({
                'administrationArea': administration_area,
                'parentAdministrationArea': parent_administration_area,
                'username': user.username,
                'fullName': user.get_full_name(),
                'status': user.status,
                'contract': user.contact,
                'telephone': user.telephone,
                'projectMobileNumber': user.project_mobile_number,
                'totalReport': total_report,
                'percent': percent_threshold,
            })

        return Response(results)


# deprecated ? No, old mobile version app used.
@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def summary_by_show_area_detail(request):
    return summary_by_show_authority_detail(request)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def summary_by_show_authority_detail(request):
    if request.QUERY_PARAMS.get('authorityId'):
        try:
            authority = Authority.objects.get(id=request.QUERY_PARAMS.get('authorityId'))
        except Authority.DoesNotExist:
            return Response({"authorityId": "Invalid authorityId. authorityId does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"authorityId": "authorityId is required."},
                        status=status.HTTP_400_BAD_REQUEST)

    if request.QUERY_PARAMS.get('tz'):
        offset_timezone = int(request.QUERY_PARAMS.get('tz'))
    else:
        offset_timezone = 0

    month = request.QUERY_PARAMS.get('month')
    try:
        month_start = datetime.datetime.strptime(month, '%m/%Y')
        month_end = month_start + relativedelta(months=+1, days=-1)
    except:
        return Response({"month": "Invalid month. Please try again. (eg. 1/2015)"},
                        status=status.HTTP_400_BAD_REQUEST)
    else:
        reporters = {}

        try:
            time_ranges = json.loads(Configuration.objects.get(system='web.summary.area', key='time_ranges').value)
        except:
            time_ranges = [
                {'startTime': 0.0, 'endTime': 6.0},
                {'startTime': 6.0, 'endTime': 12.0},
                {'startTime': 12.0, 'endTime': 18.0},
                {'startTime': 18.0, 'endTime': 24.0},
            ]

        report_types = ReportType.objects.order_by('id')
        result = AreaDetail(authority.id, authority.name, authority.get_parent_name(), '', '', report_types,
                            time_ranges)

        all_authorities = list(authority.get_children_all())
        all_authorities.append(authority.id)

        authority_users = []
        for _authority in Authority.objects.filter(id__in=all_authorities):
            for user in _authority.users.filter(
                            Q(status=USER_STATUS_VOLUNTEER) | Q(status=USER_STATUS_ADDITION_VOLUNTEER)):
                name = user.get_full_name() or user.username
                reporters[user.id] = ReporterDetail(id=user.id, full_name=name, status=user.status,
                                                    thumbnail_avatar_url=user.thumbnail_avatar_url,
                                                    administration_area=authority.id,
                                                    report_types=report_types, time_ranges=time_ranges)
                authority_users.append(user)

        reports = Report.objects.filter(created_by__in=authority_users)
        reports = reports.filter(date__range=(month_start + datetime.timedelta(hours=offset_timezone),
                                              month_end + datetime.timedelta(hours=offset_timezone)))
        reports = reports.exclude(test_flag=True).values('type', 'form_data', 'date', 'created_by', 'negative')

        for report in reports:
            form_data = json.loads(report['form_data'])
            animal_type = {}

            if form_data.get('animalType'):
                animal_type = {
                    'name': form_data.get('animalType'),
                    'sick': int(form_data.get('sickCount')) if form_data.get('sickCount') else 0,
                    'death': int(form_data.get('deathCount')) if form_data.get('deathCount') else 0,
                    'total': int(form_data.get('totalCount')) if form_data.get('totalCount') else 0,
                    'nearBy': int(form_data.get('nearByCount')) if form_data.get('nearByCount') else 0
                }

            created_by_hours = report['date'].hour % 24
            report_date = (report['date']).strftime('%d-%m-%Y')
            reporters[int(report['created_by'])].put_report(
                type=report['type'],
                report_animal_type=animal_type,
                report_negative=report['negative'],
                report_date=report_date,
                created_by_hour=created_by_hours
            )

        for key, reporter in iteritems(reporters):
            result.put_reporter(reporter)

        grade = 'A' if result.countDayReport > 20 else 'B' if result.countDayReport > 10 else 'C'
        result.set_grade(grade)

        return Response(json.loads(json.dumps(result, default=lambda o: o.__dict__)))


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def summary_by_show_performance_user(request):
    return daily_summary_performance_user(request)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def summary_by_report_detail(request):
    date_start = request.QUERY_PARAMS.get('dateStart')
    date_end = request.QUERY_PARAMS.get('dateEnd')

    try:
        date_start = datetime.datetime.strptime(date_start, '%d/%m/%Y')
    except TypeError:
        return Response({"dateStart": "Invalid dateStart. Please try again. (eg. 01/01/2015)"},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        date_end = datetime.datetime.strptime(date_end, '%d/%m/%Y')
        date_end = date_end.replace(minute=59, hour=23, second=59)
    except TypeError:
        return Response({"dateEnd": "Invalid dateEnd. Please try again. (eg. 01/01/2015)"},
                        status=status.HTTP_400_BAD_REQUEST)

    else:
        duration = date_end - date_start
        if duration.days > 31:
            return Response({"dateEnd": "Date range must less than 31 days"},
                            status=status.HTTP_400_BAD_REQUEST)
        results = []

        # GET Report type
        allowed_report_type_ids = filter_permitted_report_types(request.user)
        report_types = {}
        report_type_ids = []
        header_template = {}
        header_report_type_ids = []

        try:
            if request.GET.getlist('type__in'):
                request_type_ids = request.GET.getlist('type__in')
                header_report_type_ids = []
                for request_type_id in request_type_ids:
                    if int(request_type_id) in allowed_report_type_ids:
                        header_report_type_ids.append(request_type_id)

        except ValueError:
            pass

        if len(header_report_type_ids) == 0:
            header_report_type_ids = filter_permitted_report_types(request.user)

        for rt in ReportType.objects.filter(id__in=header_report_type_ids):
            if rt.summary_template:
                template = json.loads(rt.summary_template)
                report_type = ReportTypeTemplate(
                    id=rt.id,
                    name=rt.name,
                    template=template,
                )
                report_types[rt.id] = report_type
                report_type_ids.append(u'%s' % rt.id)

                for key, value in iteritems(template):
                    weight = 1
                    if 'weight' in value:
                        weight = value['weight']

                    try:
                        header_template[key][rt.id] = weight
                    except (KeyError, ValueError):
                        header_template[key] = {rt.id: weight}

                        header_template[key][rt.id] = weight

        # Update ordering header list
        ordering = {}
        for key, value in iteritems(header_template):
            ordering_fields = sorted(value.items(), key=operator.itemgetter(1), reverse=True)
            if ordering_fields:
                ordering[key] = ordering_fields[0][1]

        header_template['ordering'] = ordering
        ordering_header_template = sorted(header_template['ordering'].items(), key=operator.itemgetter(1), reverse=True)

        # GET header
        headers = []
        for header in ordering_header_template:
            if header[1] > -1:
                headers.append(header[0])

        if not headers:
            return Response([])

        # GET Report
        q = ''
        params = {}
        for key, val in request.QUERY_PARAMS.items():
            if key not in ['page', 'page_size', 'dateStart', 'dateEnd', 'authority']:
                if '__in' in key:
                    in_values = request.QUERY_PARAMS.getlist(key)
                    if in_values:
                        params[key] = filter(None, in_values)
                        if not params[key]:
                            del params[key]
                else:
                    params[key] = request.QUERY_PARAMS.get(key)

        if params.get('type__in'):
            report_type_ids = set(params['type__in']) & set(report_type_ids)

        if request.QUERY_PARAMS.get('authority'):
            area_ids = Authority.objects.get(id=request.QUERY_PARAMS.get('authority')).administration_areas.values_list(
                'id', flat=True)
            params['administrationArea__in'] = area_ids

        params['type__in'] = report_type_ids
        params['date__range'] = (date_start, date_end)

        reports = _search(q, request.user, params=params)

        if params.get('tags__in'):

            area_ids = []
            if not params.get('administrationArea__in'):
                areas = AdministrationArea.objects.filter(authority__tags__name__in=params['tags__in'])
                areas = get_administration_area_and_descendants(areas)
                area_ids = areas.values_list('id', flat=True)

            if area_ids:
                del params['tags__in']
                params['administrationArea__in'] = area_ids
                _reports = _search(q, request.user, params=params)
                reports = set(reports) | set(_reports)

        # Mapping
        for report in reports:
            result = collections.OrderedDict()
            report_type = report_types[report.type]
            # print headers
            for header in headers:
                if header == 'ordering':
                    continue

                if header in (report_type.get_template()):
                    try:
                        data = report.__dict__
                        data = multi_level_dict_to_one_level_dict(data)

                        if 'field' in report_type.get_template()[header]:
                            template_header = report_type.get_template()[header]['field']
                            if template_header in data:
                                result[header] = data[template_header]
                            else:
                                result[header] = template_header
                        else:
                            result[header] = '-'

                    except KeyError:
                        result[header] = '-'
                else:
                    result[header] = '-'

            if result not in results:
                results.append(result)

        # Return result
        return Response(results)


def _summary_report_visualization(request, current_domain_id=None, authority_id=None):
    from common.models import get_current_domain_id
    from summary import ReportType as SummaryReportType

    period = request.QUERY_PARAMS.get('period') or 'month'
    filter_report_types = request.QUERY_PARAMS.getlist('reportTypes')
    subscribes = request.QUERY_PARAMS.get('subscribe') == 'true'

    _report_types = ReportType.objects.all()
    if not request.user.is_staff:
        permitted_report_types = filter_permitted_report_types(request.user, subscribes=subscribes)
        _report_types = ReportType.objects.filter(id__in=permitted_report_types)

    if authority_id:
        permitted_report_types = filter_permitted_report_types_by_authorities(request.user.domain_id, authority_id,
                                                                              subscribes=subscribes)
        _report_types = ReportType.objects.filter(id__in=permitted_report_types)

    if filter_report_types:
        _report_types = _report_types.filter(id__in=filter_report_types)

    body = get_elastic_search_body(request.user, authority_id=authority_id, subscribes=subscribes)
    body['aggregations']['reportType']['aggregations'] = {
        "articles_over_time": {
            "date_histogram": {
                "field": "date",
                "interval": period,
                "format": "yyyy-MM-dd",
                "min_doc_count": 0,
            }
        }
    }
    if request.QUERY_PARAMS.get('lastWeek'):
        body = get_elastic_search_body(request.user, date_gte='now-7d', subscribes=subscribes)
        body['aggregations']['reportType']['aggregations'] = {
            "articles_over_time": {
                "date_histogram": {
                    "field": "date",
                    "interval": "day",
                    "format": "yyyy-MM-dd",
                    "min_doc_count": 0,
                    "extended_bounds": {
                        "min": "now-7d",
                        "max": "now"
                    }
                }
            }
        }

    current_domain_id = current_domain_id or get_current_domain_id(request.user)
    if current_domain_id:
        body['filter'] = {'term': {'domain': current_domain_id}}

    body = json.dumps(body)

    es = get_elasticsearch_instance()

    index = settings.HAYSTACK_CONNECTIONS['default']['INDEX_NAME']
    if not index:
        index = 'haystack'

    _time_keys = []
    _tmp_report_type = {}
    reports = es.search(index=index, doc_type='modelresult', body=body, search_type='count')
    for report_type in reports['aggregations']['reportType']['buckets']:
        report_type_id = int(report_type['key'])
        try:
            for time in report_type['articles_over_time']['buckets']:
                if not time['key_as_string'] in _time_keys:
                    _time_keys.append(time['key_as_string'])
                _tmp_report_type[report_type_id, time['key_as_string']] = time['doc_count']
        except KeyError:
            pass

    results = {}
    for report_type in _report_types:
        rt = SummaryReportType(id=report_type.id, name=report_type.name)
        for _time_key in _time_keys:
            try:
                rt.data.append({
                    'y': _tmp_report_type[report_type.id, _time_key],
                    'time': _time_key
                })
            except KeyError:
                rt.data.append({
                    'y': 0,
                    'time': _time_key
                })
        results[report_type.id] = rt

    serializer = ReportSummarySerializer(results.values(), many=True)
    return serializer.data


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def summary_report_visualization(request):
    result = _summary_report_visualization(request)
    return Response(result)


def _summary_dashboard_visualization(request, current_domain_id=None, authority_id=None):
    subscribes = request.QUERY_PARAMS.get('subscribe') == 'true'
    body = get_elastic_search_body(request.user, authority_id=authority_id, subscribes=subscribes)

    from common.models import get_current_domain_id
    current_domain_id = current_domain_id or get_current_domain_id(request.user)
    if current_domain_id:
        body['filter'] = {'term': {'domain': current_domain_id}}

    body = json.dumps(body)

    es = get_elasticsearch_instance()

    index = settings.HAYSTACK_CONNECTIONS['default']['INDEX_NAME']
    if not index:
        index = 'haystack'

    reports = es.search(index=index, doc_type='modelresult', body=body, search_type='count')

    positive_reports = 0
    negative_reports = 0
    for report_type in reports['aggregations']['reportType']['buckets']:
        if report_type['key'] == 0:
            positive_reports += report_type['doc_count']
        else:
            negative_reports += report_type['doc_count']

    ROLE_USER = [
        USER_STATUS_VOLUNTEER,
        USER_STATUS_ADDITION_VOLUNTEER,
        USER_STATUS_CAREGIVER,
    ]

    all_user_count = 0
    role_users = {}
    if request.user.is_staff and not authority_id:
        for role in ROLE_USER:
            users = User.objects.filter(status=role).values_list('id', flat=True)
            role_users[role] = len(users)
            all_user_count += len(users)

    else:
        for role in ROLE_USER:
            if authority_id:
                users = filter_permitted_users_by_authorities(request.user.domain_id, authority_id,
                                                              subscribes=subscribes, status="'%s'" % role)
            else:
                users = filter_permitted_users(request.user, subscribes=subscribes, status="'%s'" % role)

            role_users[role] = len(users)
            all_user_count += len(users)

    return {
        'users': all_user_count,
        'roleUsers': role_users,
        'positiveReports': positive_reports,
        'negativeReports': negative_reports,
    }


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def summary_dashboard_visualization(request):
    result = _summary_dashboard_visualization(request)
    return Response(result)


def get_reports_from_area(reports):
    result = {'count': len(reports)}
    administration_areas_ids = []
    administration_areas = {}
    for report in reports:
        try:
            administration_areas[report.administrationArea]['reports'].append(ReportListESSerializer(report).data)
        except:
            administration_areas[report.administrationArea] = {'reports': [
                ReportListESSerializer(report).data
            ]}
        administration_areas_ids.append(report.administrationArea)

    _administration_areas = AdministrationArea.objects.filter(id__in=administration_areas_ids)
    result['administrationAreas'] = []
    for area in _administration_areas:
        _area = AdministrationAreaListSerializer(area).data
        _area['reports'] = administration_areas[area.id]['reports']
        result['administrationAreas'].append(_area)
    return result


@api_view(['GET'])
def summary_report_by_authority(request):
    authority_id = request.QUERY_PARAMS.get('authority')
    try:
        authority = Authority.objects.get(id=authority_id)
    except Authority.DoesNotExist:
        raise Http404

    date_start = request.QUERY_PARAMS.get('dateStart')
    date_end = request.QUERY_PARAMS.get('dateEnd')

    try:
        date_start = datetime.datetime.strptime(date_start, '%d/%m/%Y')
    except TypeError:
        return Response({"dateStart": "Invalid dateStart. Please try again. (eg. 01/01/2015)"},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        date_end = datetime.datetime.strptime(date_end, '%d/%m/%Y')
    except TypeError:
        return Response({"dateEnd": "Invalid dateEnd. Please try again. (eg. 01/01/2015)"},
                        status=status.HTTP_400_BAD_REQUEST)

    else:
        result = dict()
        result['authority'] = AuthorityListSerializer(authority).data

        q = ''
        params = {}
        area_ids = authority.administration_areas.values_list('id', flat=True)
        params['negative'] = True
        params['administrationArea__in'] = area_ids
        params['date__range'] = (date_start, date_end)
        user = authority.users.all()[0] if authority.users.all() else None

        if not user:
            return Response({"authority": "Invalid Authority"},
                            status=status.HTTP_400_BAD_REQUEST)

        # outbreak
        params['stateName'] = 'Outbreak'
        reports = _search(q, user, params=params)
        result['outbreaks'] = get_reports_from_area(reports)

        # suspect-outbreak
        params['stateName'] = 'Suspect Outbreak'
        reports = _search(q, user, params=params)
        result['suspectOutbreaks'] = get_reports_from_area(reports)

        # case, report
        del params['stateName']
        params['stateName__in'] = ['Case', 'Report', 'Insignificant Report']
        reports = _search(q, user, params=params)
        result['cases'] = get_reports_from_area(reports)

        # Return result
        return Response(result)


def _daily_summary_performance_user(request, authority_id=None):
    month = request.QUERY_PARAMS.get('month')

    try:
        month_start = datetime.datetime.strptime(month, '%m/%Y')
        month_end = month_start + relativedelta(months=+1, days=-1)
    except:
        return Response({"month": "Invalid month. Please try again. (eg. 1/2015)"},
                        status=status.HTTP_400_BAD_REQUEST)

    if request.QUERY_PARAMS.get('tz'):
        offset_timezone = int(request.QUERY_PARAMS.get('tz'))
    else:
        offset_timezone = 0

    dates = []
    delta = month_end - month_start
    for i in range(delta.days + 1):
        date = month_start + datetime.timedelta(days=i)
        dates.append(date)

    results = []
    users = User.objects.filter(is_deleted=False).filter(Q(status=USER_STATUS_VOLUNTEER) |
                                                      Q(status=USER_STATUS_ADDITION_VOLUNTEER)).order_by('id')

    # not staff
    subscribes = request.QUERY_PARAMS.get('subscribe') == 'true'
    if not request.user.is_staff:
        user_ids = filter_permitted_users(request.user, subscribes=subscribes)
        users = users.filter(id__in=user_ids)

    if authority_id or request.QUERY_PARAMS.get('authorityId'):
        authority = request.QUERY_PARAMS.get('authorityId') or authority_id
        user_ids = filter_permitted_users_by_authorities(request.user.domain_id, authority, subscribes=subscribes)
        users = users.filter(id__in=user_ids)

    if request.QUERY_PARAMS.get('page_size'):
        page_size = int(request.QUERY_PARAMS.get('page_size'))
        users = users[:page_size]

    reporters = {}
    for user in users:
        reporters[user.id] = MonthlyReporter(name=user.get_full_name() or user.username, dates=[])

    reports = Report.objects.filter(created_by__in=users)
    reports = reports.filter(date__range=(month_start + datetime.timedelta(hours=offset_timezone),
                                          month_end + datetime.timedelta(hours=offset_timezone)))
    reports = reports.exclude(test_flag=True).values('created_by', 'date')

    for report in reports:
        try:
            date = (report['date'] + datetime.timedelta(hours=offset_timezone)).strftime('%d-%m-%Y')
            if date not in reporters[int(report['created_by'])].dates:
                reporters[int(report['created_by'])].dates.append(date)
        except KeyError:
            pass

    for key, reporter in iteritems(reporters):
        total = len(reporter.dates)
        active_dates = reporter.dates

        results.append({
            'fullName': reporter.name,
            'activeDates': active_dates,
            'numberOfActiveDays': total,
            'grade': 'A' if total > 20 else 'B' if total > 10 else 'C'
        })

    return results


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def daily_summary_performance_user(request):
    results = _daily_summary_performance_user(request)
    return Response(results)
