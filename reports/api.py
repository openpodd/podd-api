# -*- encoding: utf-8 -*-
import re
from calendar import Calendar
from copy import deepcopy
import datetime
import json
import os
import uuid
from cacheops import invalidate_obj
from crum import set_current_user

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.timezone import UTC

from dateutil.relativedelta import relativedelta

from rest_framework import viewsets, status, filters
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.compat import RequestFactory
from rest_framework.decorators import api_view, action, authentication_classes, link, permission_classes, list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import GroupReportType, User, Configuration, Authority
from accounts.serializers import UserSerializer
from common.constants import PRIORITY_FOLLOW, GROUP_WORKING_TYPE_REPORT_TYPE, PRIORITY_IGNORE, \
    SUPPORT_LIKE_ME_TOO_COMMENT, SUPPORT_ME_TOO_COMMENT, SUPPORT_LIKE_ME_TOO, SUPPORT_LIKE_COMMENT, SUPPORT_LIKE, \
    SUPPORT_ME_TOO, SUPPORT_COMMENT, STATUS_PUBLISH, STATUS_DELETE, PARENT_TYPE_MERGE
from common.functions import (has_permission_on_report_type, has_permission_on_administration_area,
    upload_to_s3, filter_permitted_administration_areas_and_descendants, resize_and_crop,
    publish_into_rabbitmq, get_public_area, filter_permitted_report_types, filter_permitted_administration_areas_and_descendants_by_authorities)
from common.models import get_current_domain_id
from common.podd_elasticsearch import get_elasticsearch_instance
from feed.api import get_area_from_feed
from flags.functions import create_flag_comment
from flags.serializers import FlagSerializer
from logs.models import LogItem, LogAction
from mentions.functions import create_mentions
from notifications.models import Notification
from plans.models import PlanReport
from plans.serializers import PlanReportSerializer
from reports import Area
from reports import tasks
from reports.functions import _search
from reports.models import Report, ReportType, ReportComment, AdministrationArea, ReportState, CaseDefinition, \
    ReportTypeCategory, ReportLike, ReportMeToo, ReportAbuse, AnimalLaboratoryCause, ReportLaboratoryItem, \
    ReportLaboratoryFile, ReportLaboratoryCase, ReportImage, ReportAccomplishment
from reports.paginations import PaginatedReportListESSerializer, PaginatedReportListESWFormDataSerializer, PaginatedReportListESLiteSerializer, \
    PaginatedAdministrationContactSerializer, PaginatedReportListFullSerializer
from reports.pub_tasks import publish_report_flag
from reports.serializers import (ReportSerializer, ReportListESSerializer, ReportTypeSerializer,
                                 ReportTypeListSerializer, ReportImageSerializer, ReportCommentSerializer,
                                 DashboardSerializer,
                                 AdministrationAreaSerializer, ReportStateSerializer, CaseDefinitionSerializer,
                                 ReportTypeCategorySerializer,
                                 ReportLikeSerializer, ReportMeTooSerializer, AdministrationAreaDetailSerializer,
                                 ReportAbuseSerializer,
                                 AdministrationAreaContactSerializer, AdministrationAreaListSerializer,
                                 AnimalLaboratoryCauseSerializer,
                                 ReportLaboratoryItemSerializer, CaseDefinitionExplainedSerializer,
                                 ReportAccomplishmentSerializer)
from reports.pub_tasks import publish_report, publish_comment, publish_report_image
from reports.search_indexes import ReportIndex

from haystack import connections as haystack_connections


class ReportTypeCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    model = ReportTypeCategory
    serializer_class = ReportTypeCategorySerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return ReportTypeCategory.objects.all()


class ReportTypeViewSet(viewsets.ModelViewSet):
    model = ReportType
    serializer_class = ReportTypeSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        query = ReportType.objects.filter(id__gt=0).order_by('weight', 'name')

        category = self.request.QUERY_PARAMS.get('category', None)
        if category:
            query = query.filter(categories=category)

        return query

    # @cache_response(60 * 5)
    def list(self, request):
        #self.get_queryset() # call for retrieve cache
        queryset = self.get_queryset()
        if not request.GET.get('include_system'):
            queryset = queryset.filter(is_system=False)

        subscribes = request.GET.get('subscribes')
        if not request.user.is_staff:
            queryset = queryset.filter(id__in=filter_permitted_report_types(request.user, subscribes=subscribes))
            queryset = queryset.filter(Q(user_status='') | Q(user_status__icontains=(request.user.status or '')))

        serializer = ReportTypeListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk, *args, **kwargs):

        #self.object = self.get_object() # unuse for retrieve cache
        try:
            self.object = ReportType.objects.get(id=pk)
        except ReportType.DoesNotExist:
            return Response({u'detail': u'report type not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        if has_permission_on_report_type(user=request.user, report_type=self.object):
            serializer = self.get_serializer(self.object)
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)


class AdministrationAreaViewSet(viewsets.ModelViewSet):
    model = AdministrationArea
    serializer_class = AdministrationAreaSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return AdministrationArea.objects.all().select_related('authority', 'parent').prefetch_related('authority__admins')

    def list(self, request):
        queryset = self.get_queryset()
        if not request.user.is_staff:
            queryset = filter_permitted_administration_areas_and_descendants(request.user, subscribes=True)

        latitude = request.QUERY_PARAMS.get('latitude')
        longitude = request.QUERY_PARAMS.get('longitude')

        parent_name = request.QUERY_PARAMS.get('parentName')
        if parent_name:
            queryset = queryset.filter(parent__name__contains=parent_name)

        if latitude and longitude:
            current_position = GEOSGeometry('POINT(%f %f)' % (float(longitude), float(latitude)), 4326)
            not_empty_queryset = queryset.filter(mpoly__covers=current_position)

            if not_empty_queryset.count() == 0:
                queryset = [get_public_area()]
            else:
                queryset = not_empty_queryset
        else:
            queryset = queryset.order_by('weight', 'name')

        serializer = AdministrationAreaListSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        if request.user.is_public or request.QUERY_PARAMS.get('public'):
            return get_area_from_feed(request, pk)

        queryset = self.get_queryset()
        administration_area = get_object_or_404(queryset, pk=pk)

        if has_permission_on_administration_area(user=request.user, administration_area=administration_area, subscribes=True):
            serializer = AdministrationAreaSerializer(administration_area)
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                                status=status.HTTP_403_FORBIDDEN)


def _view_administration_area_contacts(request, authority_id=None, is_paginator=True):
    queryset = AdministrationArea.objects.all()
    if not request.user.is_staff:
        queryset = filter_permitted_administration_areas_and_descendants(request.user, subscribes=False)

    if authority_id:
        queryset = filter_permitted_administration_areas_and_descendants_by_authorities(request.user.domain_id, authority_id, subscribes=False)

    starts_with = request.QUERY_PARAMS.get('name__startsWith')
    if starts_with:
        queryset = queryset.filter(name__startswith=starts_with)

    keywords = request.QUERY_PARAMS.getlist('keywords')
    if keywords:
        for keyword in keywords:
            queryset = queryset.filter(address__contains=keyword)

    alphabet = request.QUERY_PARAMS.get('alphabet')
    if alphabet:

        query = Q(name__startswith=u'%s%s' % (starts_with, alphabet))

        thai_vowels = [u'ไ', u'ใ', u'โ', u'เ', u'แ']
        for thai_vowel in thai_vowels:
            query = query | Q(name__startswith=u'%s%s%s' % (starts_with, thai_vowel, alphabet))

        queryset = queryset.filter(query)
        queryset = queryset.order_by('name')

    queryset = queryset.order_by('id')

    page_size = request.QUERY_PARAMS.get('page_size') or 200000
    paginator = Paginator(queryset, page_size)
    page = request.QUERY_PARAMS.get('page')

    if is_paginator:
        try:
            administration_areas = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            administration_areas = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999),
            # deliver last page of results.
            administration_areas = paginator.page(paginator.num_pages)

        serializer = PaginatedAdministrationContactSerializer(administration_areas)

    else:
        administration_areas = queryset[:page_size]
        serializer = AdministrationAreaContactSerializer(administration_areas, many=True)
    return serializer.data


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def view_administration_area_contacts(request):
    result = _view_administration_area_contacts(request)
    return Response(result)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def update_administration_area_contacts(request):
    data = request.DATA

    queryset = AdministrationArea.objects.all()
    if not request.user.is_staff:
        queryset = filter_permitted_administration_areas_and_descendants(request.user, subscribes=False)

    permission_areas = queryset.values_list('id', flat=True)

    for area in data:
        try:
            if not area['id'] in permission_areas:
                continue

            administration_area = AdministrationArea.objects.get(id=area['id'])
            administration_area.contacts = area['contacts']
            administration_area.save()
        except AdministrationArea.DoesNotExist:
            pass

    return Response({})


class ReportStateViewSet(viewsets.ModelViewSet):
    model = ReportState
    serializer_class = ReportStateSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        queryset = ReportState.objects.all().order_by('weight', 'id')
        report_type_id = self.request.QUERY_PARAMS.get('reportType', None)
        if report_type_id is not None:
            queryset = queryset.filter(report_type__id=report_type_id)
        return queryset


class CaseDefinitionViewSet(viewsets.ModelViewSet):
    model = CaseDefinition
    serializer_class = CaseDefinitionSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        # queryset = CaseDefinition.objects.filter(report_type__id=filter_permitted_report_types(self.request.user))
        queryset = CaseDefinition.objects.all()
        report_type_id = self.request.QUERY_PARAMS.get('reportType', None)
        if report_type_id is not None:
            queryset = queryset.filter(report_type__id=report_type_id)
        return queryset

    @list_route()
    def explained(self, request, pk=None):
        queryset = self.get_queryset()

        if queryset.count() is not 0:
            serializer = CaseDefinitionExplainedSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)



def ignore(report, user=None):
    if not user:
        from common.functions import get_system_user
        user = get_system_user()

    comment = create_flag_comment(report=report, priority=PRIORITY_IGNORE, flag_owner=user)
    serializer = FlagSerializer(data={
        'reportId': report.id,
        'priority': PRIORITY_IGNORE,
    })
    if serializer.is_valid():
        serializer.object.comment = comment
        serializer.object.flag_owner = user
        serializer.save()

        publish_report_flag(serializer.data)

    # SET REPORT NEGATIVE TO FALSE
    report.negative = False
    report.save()


class ReportViewSet(viewsets.ModelViewSet):
    model = Report
    serializer_class = ReportSerializer
    pagination_serializer_class = PaginatedReportListESSerializer
    paginate_by = 20
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return Report.objects.all()

    def _get_report_type_from_report_type_code(self, request):
        report_type_code = request.DATA.get('reportTypeCode')
        if report_type_code:
            try:
                return ReportType.objects.get(code=report_type_code)
            except ReportType.DoesNotExist:
                return None

    def pre_save(self, obj):
        if not obj.id:
            obj.created_by = self.request.user
            obj.original_form_data = obj.original_form_data or {}
            obj.original_form_data = json.dumps(obj.original_form_data)
        else:
            obj.updated_by = self.request.user

        obj.form_data = obj.form_data or {}
        obj.form_data = json.dumps(obj.form_data)
        obj.date = obj.date.astimezone(UTC())
        follow_flag = self.request.DATA.get('followFlag', 0)
        if follow_flag == PRIORITY_FOLLOW:
            try:
                obj.parent = Report.objects.get(guid=self.request.DATA.get('parentGuid'))
            except Report.DoesNotExist:
                pass

    def post_save(self, obj, created=False):

        if obj.negative:
            LogItem.objects.log_action(key='REPORT_CREATE', created_by=obj.created_by, object1=obj)
            if settings.ESPER_CONNECTION_URL:
                pass
            else:
                tasks.new_negative_report_rule.delay(obj) # deprecate when authority comes...

    def create(self, request):

        parent = None
        if not request.DATA.get("parent") and request.DATA.get('parentGuid'):
            try:
                parent = Report.objects.get(guid=request.DATA['parentGuid'])
            except Report.DoesNotExist:
                return Response({u'detail': u'parentGuid does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        if parent:
            request.DATA['parent'] = parent.id

        data = request.DATA
        if not data.get('reportTypeId'):
            # Do nothing if request already specify report type id.
            report_type = self._get_report_type_from_report_type_code(request)
            if report_type:
                data['reportTypeId'] = report_type.id

        serializer = ReportSerializer(data=data, context={'request': request})

        # make this api idempotent
        # if client submit data with same reportId and guid
        # we will assume that this is the same transaction as the previous one
        # so we will do nothing and answer http code = 201
        if not data.get('reportId'):
            return Response({u'reportId': [u'This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        if not data.get('guid'):
            return Response({u'guid': [u'This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        oldReport = Report.objects.filter(report_id=data.get('reportId'), guid=data.get('guid')).first()
        if oldReport:
            return Response(status=status.HTTP_201_CREATED, headers=self.get_success_headers(serializer.data))

        if serializer.is_valid():
            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)

            headers = self.get_success_headers(serializer.data)

            return Response(status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        report = get_object_or_404(queryset, pk=pk)

        if (has_permission_on_administration_area(user=request.user, administration_area=report.administration_area, subscribes=True)) or \
           (request.user.is_public and report.curated_in.count()):

            if request.user.is_public:
                report.comment_count = report.comments.filter(created_by__is_public=True, state__isnull=True).count()

            serializer = ReportSerializer(report)
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

    def list(self, request):
        q = request.QUERY_PARAMS.get('q')
        params = {}
        for key, val in request.QUERY_PARAMS.items():
            if key not in ['q', 'page', 'page_size', 'withFormData', 'lite', 'withSummary', 'isPublic']:
                if '__in' in key:
                    params[key] = request.QUERY_PARAMS.getlist(key)
                else:
                    params[key] = request.QUERY_PARAMS.get(key)

        if request.QUERY_PARAMS.get('isPublic'):
            areas = AdministrationArea.objects.filter(code__startswith='public').values_list('id', flat=True)
            params['administrationArea__in'] = areas

        queryset = _search(q, request.user, params=params)

        page_size = request.QUERY_PARAMS.get('page_size') or self.get_paginate_by()
        paginator = Paginator(queryset, page_size)
        page = request.QUERY_PARAMS.get('page')

        try:
            reports = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            reports = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999),
            # deliver last page of results.
            reports = paginator.page(paginator.num_pages)

        if request.QUERY_PARAMS.get('withFormData'):
            pagination_serializer_class = PaginatedReportListESWFormDataSerializer
        elif request.QUERY_PARAMS.get('lite'):
            pagination_serializer_class = PaginatedReportListESLiteSerializer
        else:
            pagination_serializer_class = self.pagination_serializer_class

        serializer = pagination_serializer_class(reports)

        summary = request.QUERY_PARAMS.get('withSummary')

        if summary:
            results = []

            start_date = datetime.date(2015, 1, 1)
            end_date = datetime.datetime.now().date()

            delta = end_date - start_date
            days = int(delta.total_seconds() / (60 * 60 * 24))

            date_list = [(end_date - datetime.timedelta(days=x)).strftime('%Y-%m-%d') for x in range(0, days + 1)]

            summary_months = queryset.date_facet('date', start_date=start_date, end_date=end_date, gap_by='day').facet_counts()
            for summary_month in summary_months['dates']['date']:
                date = summary_month[0].strftime('%Y-%m-%d')
                results.append({'date': date, 'count': summary_month[1]})
                date_list.remove(date)

            for date in date_list:
                results.append({'date': date, 'count': 0})

            results.sort(key=lambda x: x['date'], reverse=False)
            serializer.data['summary'] = results

        return Response(serializer.data)

    def update(self, request, pk=None):
        return Response({"detail": "Method 'PUT' not allowed."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, pk=None):
        return Response({"detail": "Method 'DELETE' not allowed."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @link()
    def comments(self, request, pk=None):
        report = self.get_object()
        if (has_permission_on_report_type(user=request.user, report_type=report.type) and \
            has_permission_on_administration_area(user=request.user, administration_area=report.administration_area, subscribes=True)):
            queryset = ReportComment.objects.filter(report=report)
            if request.user.is_public:
                queryset = queryset.filter(created_by__is_public=True, state__isnull=True)
            serializer = ReportCommentSerializer(queryset, many=True)
            serializer_context = {'request': request}
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                        status=status.HTTP_403_FORBIDDEN)

    @action()
    def comment(self, request, pk=None):
        request.DATA['reportId'] = pk
        serializer = ReportCommentSerializer(data=request.DATA, context={'request': request})
        if serializer.is_valid():
            if (has_permission_on_administration_area(user=request.user, administration_area=serializer.object.report.administration_area)):
                if request.FILES.get('file'):
                    file = request.FILES.get('file')
                    if file.size <= settings.MAX_ATTACH_FILE_COMMENT_SIZE:
                        file_url = upload_to_s3(file)
                        if file_url:
                            serializer.object.file_url = file_url
                        else:
                            return Response({"detail": "Cannot upload your file"},
                                status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({"detail": "Cannot upload file size > 10 MB"},
                            status=status.HTTP_400_BAD_REQUEST)

                serializer.object.message = strip_tags(serializer.object.message)
                serializer.object.created_by = request.user
                serializer.save()

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({u'detail': u'You do not have permission to perform this action.'},
                        status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @link()
    def accomplishments(self, request, pk=None):
        report = self.get_object()
        if (has_permission_on_report_type(user=request.user, report_type=report.type) and
                has_permission_on_administration_area(user=request.user,
                                                      administration_area=report.administration_area,
                                                      subscribes=True)):
            queryset = ReportAccomplishment.objects.filter(report=report)
            serializer = ReportAccomplishmentSerializer(queryset[0], many=False)
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)


    @action()
    def accomplishment(self, request, pk=None):
        data = request.DATA.copy()
        data['reportId'] = pk

        serializer = ReportAccomplishmentSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            if (has_permission_on_administration_area(user=request.user,
                                                      administration_area=serializer.object.report.administration_area)):
                target = serializer
                target.object.title = strip_tags(serializer.object.title)
                target.object.description = strip_tags(serializer.object.description)
                target.object.created_by = request.user
                target.save()

                return Response(target.data, status=status.HTTP_201_CREATED)
            else:
                return Response({u'detail': u'You do not have permission to perform this action.'},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @link()
    def involved(self, request, pk=None):
        report = self.get_object()
        if (has_permission_on_report_type(user=request.user, report_type=report.type) and \
            has_permission_on_administration_area(user=request.user, administration_area=report.administration_area, subscribes=True)):

            if report.parent:
                ids = Report.objects.filter(parent=report.parent).exclude(id=report.id).values_list('id', flat=True)
                ids = [report.parent.id] + list(ids)
            else:
                ids = Report.objects.filter(parent=report).exclude(id=report.id).values_list('id', flat=True)

            if len(ids) == 0:
                ids = [0]

            q = ''
            params = {'django_id__in': ids}
            queryset = _search(q, request.user, params=params, allowed_all_reports=True)

            serializer = ReportListESSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                        status=status.HTTP_403_FORBIDDEN)

    # deprecate
    @action()
    def follow(self, request, pk=None):
        report = self.get_object()
        if (has_permission_on_administration_area(user=request.user, administration_area=report.administration_area)):

            parent_id = request.DATA.get('parent', '')
            if not parent_id:
                return Response({u'parent': u'This field is required.'},
                    status=status.HTTP_400_BAD_REQUEST)

            try:
                parent = Report.objects.get(id=parent_id)
            except Report.DoesNotExist:
                return Response({u'parent': u'Report not found.'},
                    status=status.HTTP_400_BAD_REQUEST)

            # CREATE REPORT COMMENT FLAG
            comment = create_flag_comment(report=report, priority=PRIORITY_FOLLOW, flag_owner=request.user)
            serializer = FlagSerializer(data={
                'reportId': report.id,
                'priority': PRIORITY_FOLLOW,
            })
            if serializer.is_valid():
                serializer.object.comment = comment
                serializer.object.flag_owner = request.user
                serializer.save()

                publish_report_flag(serializer.data)

            report.parent = parent
            report.save()
            return Response()
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN)

    @action()
    def state(self, request, pk=None):
        report = self.get_object()

        try:
            report.updated_by = request.user
            report.state = ReportState.objects.get(id=request.DATA.get('stateId', None), report_type=report.type)
            report.save()
        except ReportState.DoesNotExist:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN)

        return Response({})

    @action()
    def tags(self, request, pk=None):
        report = self.get_object()
        report_index = ReportIndex()
        old_tags = list(report.tags.all().values_list('name', flat=True))
        if request.DATA.get('tags') or request.DATA.get('tags') == []:
            try:
                report.tags.clear()

                tags_text = ''
                for tag in request.DATA.get('tags'):
                    tags_text = '%s [tag:%s]' % (tags_text, tag['text'])
                    report.tags.add(tag['text'])
                report_index.update_object(report)

                if not tags_text:
                    try:
                        tags_text = Configuration.objects.get(system='web.template.report', key='empty_tags').value
                    except Configuration.DoesNotExist:
                        tags_text = u'\'ไม่มีการตั้ง Tags\''

                try:
                    template_for_tags =  Configuration.objects.get(system='web.template.report', key='comment_tags').value
                except Configuration.DoesNotExist:
                    template_for_tags = u'@[%(username)s] ได้ทำตั้งค่า Tags เป็น %(tags)s'

                message = template_for_tags % {'username': request.user.username,
                    'tags': tags_text }

                comment = ReportComment.objects.create(
                    report = report,
                    message = message,
                    created_by = request.user,
                )

            except KeyError:
                report.tags.clear()
                for tag in old_tags:
                    report.tags.add(tag)

        return Response({})

    @link()
    def likes(self, request, pk=None):
        report = self.get_object()
        likes = report.likes.all().values_list('created_by', flat=True)
        queryset = User.objects.filter(id__in=likes)
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    @action()
    def like(self, request, pk=None):
        data = request.DATA.copy()
        data['reportId'] = pk

        serializer = ReportLikeSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            try:
                report = self.get_object()
                like = ReportLike.objects.get(report=report, created_by=request.user)
                serializer = ReportLikeSerializer(like)
            except ReportLike.DoesNotExist:
                serializer.object.created_by = request.user
                serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action()
    def unlike(self, request, pk=None):
        try:
            report = self.get_object()
            like = ReportLike.objects.get(report=report, created_by=request.user)
        except ReportLike.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            like.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @link()
    def metoos(self, request, pk=None):
        report = self.get_object()
        metoos = report.me_toos.all().values_list('created_by', flat=True)
        queryset = User.objects.filter(id__in=metoos)
        serializer = UserSerializer(queryset, many=True)

        return Response(serializer.data)

    @action()
    def metoo(self, request, pk=None):
        data = request.DATA.copy()
        data['reportId'] = pk

        serializer = ReportMeTooSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            try:
                report = self.get_object()
                metoo = ReportMeToo.objects.get(report=report, created_by=request.user)
                serializer = ReportMeTooSerializer(metoo)
            except ReportMeToo.DoesNotExist:
                serializer.object.created_by = request.user
                serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action()
    def unmetoo(self, request, pk=None):
        try:
            report = self.get_object()
            metoo = ReportMeToo.objects.get(report=report, created_by=request.user)
        except ReportMeToo.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            metoo.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @link()
    def reportAbuses(self, request, pk=None):
        report = self.get_object()
        report_abuses = report.report_abuses.order_by('id').values_list('created_by', flat=True)
        queryset = User.objects.filter(id__in=report_abuses)
        serializer = UserSerializer(queryset, many=True)

        return Response(serializer.data)

    @action()
    def reportAbuse(self, request, pk=None):
        data = request.DATA.copy()
        data['reportId'] = pk

        if request.user.is_anonymous:
            return Response({u'detail': u'You do not have permission to perform this action.'}
                            , status=status.HTTP_400_BAD_REQUEST)

        serializer = ReportAbuseSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            try:
                report = self.get_object()
                report_abuse = ReportAbuse.objects.get(report=report, created_by=request.user)
                serializer = ReportAbuseSerializer(report_abuse)
            except ReportAbuse.DoesNotExist:
                serializer.object.created_by = request.user
                serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action()
    def mark_to_test(self, request, pk=None):
        report = self.get_object()
        report.test_flag = True
        report.save()
        return Response(status=status.HTTP_200_OK)

    @action()
    def mark_to_untest(self, request, pk=None):
        report = self.get_object()
        report.test_flag = False
        report.save()
        return Response(status=status.HTTP_200_OK)

    @action()
    def publish(self, request, pk=None):
        if not request.user.is_superuser:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

        report = self.get_object()
        try:
            if request.QUERY_PARAMS.get('administrationArea'):
                administration_area = get_object_or_404(AdministrationArea, pk=request.QUERY_PARAMS.get('administrationArea'))
            else:
                administration_area = report.get_publish_administration_area()
            report.curate_in_administration_area(administration_area)
            return Response(status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({u'detail': ex}, status=status.HTTP_400_BAD_REQUEST)

    @action()
    def unpublish(self, request, pk=None):
        if not request.user.is_superuser:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

        report = self.get_object()
        report.remove_from_public_feed()
        return Response(status=status.HTTP_200_OK)

    @link()
    def states_logs(self, request, pk=None):
        report = self.get_object()
        if (has_permission_on_report_type(user=request.user, report_type=report.type) and
            has_permission_on_administration_area(user=request.user,
                                                  administration_area=report.administration_area,
                                                  subscribes=True)):

            log_action = LogAction.objects.get(name='REPORT_STATE_CHANGE')
            queryset = LogItem.objects.filter(action=log_action, object_id1=report.id).order_by('-created_at')

            data = []
            for log_item in queryset:
                state = ReportState.objects.get(id=log_item.object_id2)
                data.append({
                    'state': ReportStateSerializer(state).data,
                    'createdAt': log_item.created_at,
                    'createdBy': UserSerializer(log_item.created_by).data,
                })

            return Response(data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

    @link()
    def plans(self, request, pk=None):
        report = self.get_object()
        if (has_permission_on_report_type(user=request.user, report_type=report.type) and
                has_permission_on_administration_area(user=request.user,
                                                      administration_area=report.administration_area,
                                                      subscribes=True)):

            queryset = PlanReport.objects.filter(report=report).order_by('-created_at')
            serializer = PlanReportSerializer(queryset, many=True, context={'request': request})
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

    @link()
    def similar(self, request, pk=None):

        report = self.get_object()

        if not (report.negative and report.administration_area and report.administration_area.authority):
            return Response([])

        authority = report.administration_area.authority
        range_focus_days = 7
        range_focus = datetime.timedelta(days=range_focus_days)

        queryset = Report.objects.filter(
            negative=True, parent__isnull=True, administration_area__authority=authority,
            date__range=(report.date - range_focus, report.date + range_focus)
        )[0:50]
        serializer = ReportSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


    @action()
    def merge(self, request, pk=None):
        parent = self.get_object()

        if parent.parent:
            return Response(status=status.HTTP_200_OK)

        report_ids = request.DATA.get('reportIds', [])

        for report_id in report_ids:

            try:
                report = Report.objects.get(id=report_id, negative=True)
                report.parent = parent
                report.parent_type = PARENT_TYPE_MERGE
                report.save()

            except Report.DoesNotExist:
                pass


        return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def add_reports_tags(request):

    report_index = ReportIndex()

    report_ids = request.DATA.get('reportIds')
    tags = request.DATA.get('tags')

    if not report_ids:
        return Response({"reportIds": "reportIds is required."},
                            status=status.HTTP_400_BAD_REQUEST)

    if not tags:
        return Response({"tags": "tags is required."},
                            status=status.HTTP_400_BAD_REQUEST)

    reports = Report.objects.filter(id__in=report_ids)
    for report in reports:

        old_tags = list(report.tags.all().values_list('name', flat=True))
        try:
            report.tags.clear()

            tags_text = ''
            for tag in tags:
                tags_text = '%s [tag:%s]' % (tags_text, tag['text'])
                report.tags.add(tag['text'])

            report_index.update_object(report)

            if not tags_text:
                try:
                    tags_text = Configuration.objects.get(system='web.template.report', key='empty_tags').value
                except Configuration.DoesNotExist:
                    tags_text = u'\'ไม่มีการตั้ง Tags\''

            try:
                template_for_tags =  Configuration.objects.get(system='web.template.report', key='comment_tags').value
            except Configuration.DoesNotExist:
                template_for_tags = u'@[%(username)s] ได้ทำตั้งค่า Tags เป็น %(tags)s'

            message = template_for_tags % {
                'username': request.user.username,
                'tags': tags_text
            }

            comment = ReportComment.objects.create(
                report=report,
                message=message,
                created_by=request.user,
            )

        except KeyError:
            report.tags.clear()
            for tag in old_tags:
                report.tags.add(tag)

    return Response({}, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def reports_search(request):
    q = request.QUERY_PARAMS.get('q')

    try:
        tz = int(request.QUERY_PARAMS.get('tz'))
    except:
        tz = 0

    params = {}

    date__lt = request.QUERY_PARAMS.get('date__lt')
    if date__lt:
        params['date__lt'] = date__lt

    authorities = request.QUERY_PARAMS.get('authorities')
    if authorities:
        params['authorities'] = authorities.split(',')

    administration_areas = request.QUERY_PARAMS.get('administrationAreas')
    if administration_areas:
        params['administrationArea__in'] = administration_areas.split(',')

    is_parent = request.QUERY_PARAMS.get('isParent')
    if is_parent:
        params['_missing_'] = 'parent'

    queryset = _search(q, request.user, params=params, tz=tz)

    page_size = request.QUERY_PARAMS.get('page_size') or 1000
    paginator = Paginator(queryset, page_size)
    page = request.QUERY_PARAMS.get('page')

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        reports = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999),
        # deliver last page of results.
        reports = paginator.page(paginator.num_pages)

    if request.QUERY_PARAMS.get('full'):
        pagination_serializer_class = PaginatedReportListFullSerializer

    elif request.QUERY_PARAMS.get('withFormData'):
        pagination_serializer_class = PaginatedReportListESWFormDataSerializer

    else:
        pagination_serializer_class = PaginatedReportListESSerializer

    serializer = pagination_serializer_class(reports)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def add_report_image(request):

    report_guid = request.DATA.get('reportGuid') or 0
    try:
        report = Report.objects.get(guid=report_guid)
    except Report.DoesNotExist:
        return Response({'reportGuid': 'Report is not found.'}, status=status.HTTP_400_BAD_REQUEST)

    request.DATA['report'] = report.id
    serializer = ReportImageSerializer(data=request.DATA)

    # make this api idempotent
    # if client submit data with same reportId, imageUrl and guid
    # we will assume that this is the same transaction as the previous one
    # so we will do nothing and answer http code = 201
    oldImage = ReportImage.objects.filter(
        guid=request.DATA.get('guid'),
        report_id=report.id,
        image_url=request.DATA.get('imageUrl')).first()
    if oldImage:
        return Response(ReportImageSerializer(oldImage).data, status=status.HTTP_201_CREATED)

    if serializer.is_valid():
        serializer.save()

        index = haystack_connections['default'].get_unified_index().get_index(Report)
        index.update_object(report)

        data_to_publish = serializer.data
        data_to_publish['administrationAreaId'] = report.administration_area.id

        publish_report_image(data_to_publish)
        # extract image gps data
        tasks.extract_image_gps.delay(data_to_publish['guid'])

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def upload_report_image(request):
    image = request.FILES.get('image')
    if image:
        # CONVERT InMemoryUploadedFile to Image
        thumbnail = default_storage.save(image.name, ContentFile(image.read()))
        image.seek(0)

        # File path
        thumbnail_path = os.path.join(settings.MEDIA_ROOT, thumbnail)

        # resize
        resize_and_crop(thumbnail_path, thumbnail_path, (400, 400))

        # Convert Image to File
        (image_name, image_ext) = os.path.splitext(image.name)
        thumbnail_file = File(open(thumbnail_path), '%s-thumbnail%s' % (image_name, image_ext))

        # UPLOAD to S3
        image_url = upload_to_s3(image)
        thumbnail_url = upload_to_s3(thumbnail_file)

        if image_url and thumbnail_url:
            return Response({
                'imageUrl': image_url,
                'thumbnailUrl': thumbnail_url
            })
        else:
            return Response({"detail": u"อัพโหลดไฟล์ไม่สำเร็จ"},
                status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'detail': 'Image not found.'}, status=status.HTTP_400_BAD_REQUEST)


class ReportCommentViewSet(viewsets.ModelViewSet):
    model = ReportComment
    serializer_class = ReportCommentSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    ordering_fields = ('created_at', )

    def get_queryset(self):
        return ReportComment.objects.all()

    def list(self, request):
        queryset = self.get_queryset()
        report = get_object_or_404(Report, id=request.QUERY_PARAMS.get('reportId'))

        if request.QUERY_PARAMS.get('reportId'):
            queryset = queryset.filter(report=request.QUERY_PARAMS.get('reportId'))

        if request.user.is_public:
            queryset = queryset.filter(created_by__is_public=True, state__isnull=True)

        serializer = ReportCommentSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        report_comment = get_object_or_404(queryset, pk=pk)

        if (has_permission_on_report_type(user=request.user, report_type=report_comment.report.type) and \
            has_permission_on_administration_area(user=request.user, administration_area=report_comment.report.administration_area, subscribes=True)):
            serializer = ReportCommentSerializer(report_comment)
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

    def create(self, request):
        serializer = ReportCommentSerializer(data=request.DATA, context={'request': request})
        if serializer.is_valid():
            if (has_permission_on_administration_area(user=request.user,
                                                      administration_area=serializer.object.report.administration_area,
                                                      subscribes=True)):
                if request.FILES.get('file'):
                    file = request.FILES.get('file')
                    if file.size <= settings.MAX_ATTACH_FILE_COMMENT_SIZE:
                        file_url = upload_to_s3(file)
                        if file_url:
                            serializer.object.file_url = file_url
                        else:
                            return Response({"detail": u"ไม่สามารถอัพโหลดไฟล์สำเร็จ"},
                                status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({"detail": u"ไม่สามารถอัพโหลดไฟล์ที่มีขนาดของไฟล์มากกว่า 10MB"},
                            status=status.HTTP_400_BAD_REQUEST)

                serializer.object.message = strip_tags(serializer.object.message)
                serializer.object.created_by = request.user
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({u'detail': u'You do not have permission to perform this action.'},
                        status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        queryset = self.get_queryset()
        report_comment = get_object_or_404(queryset, pk=pk)

        if request.user != report_comment.created_by:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

        message = strip_tags(request.DATA.get('message'))
        if not message or message == report_comment.message:
            return Response({'detail': 'no message change.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReportCommentSerializer(report_comment, data=request.DATA, context={'request': request})
        if serializer.is_valid():
            serializer.object.message = message
            serializer.object.updated_by = request.user
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        return Response({"detail": "Method 'DELETE' not allowed."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ReportLikeViewSet(viewsets.ModelViewSet):
    model = ReportLike
    serializer_class = ReportLikeSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    ordering_fields = ('created_at', )


class ReportMeTooViewSet(viewsets.ModelViewSet):
    model = ReportMeToo
    serializer_class = ReportMeTooSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    ordering_fields = ('created_at', )


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def get_default_administration_area(request):
    user = request.user
    if user.administration_area:
        return Response({
           'success': True,
            'administartionArea': {
                'id': user.administration_area.id,
                'name': user.administration_area.name
            }
        })
    else:
        return Response({
            'success': False
        })


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def add_support(request):

    report_guid = request.DATA.get('reportGuid')
    report_id = request.DATA.get('reportId')
    message = request.DATA.get('message') or ''
    is_like = request.DATA.get('isLike')
    is_me_too = request.DATA.get('isMeToo')

    if report_guid:
        try:
            report = Report.objects.get(guid=report_guid)
        except Report.DoesNotExist:
            return Response({'reportGuid': 'Report is not found.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'reportId': 'Report is not found.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    keys_data = {'created_by': user, 'report': report}

    like, like_created = ReportLike.objects.get_or_create(**keys_data)
    if is_like:
        like.status = STATUS_PUBLISH
        like.save() if like.status is not like.var_cache['status'] else None
    elif is_like is False:
        # do only if is_like is REALLY specified with FALSE value.
        like.delete()
    elif not is_like and like_created:
        # only set to STATUS_DELETE if not specify and newly created.
        like.delete()
    if like.status is not STATUS_PUBLISH:
        like = None

    me_too, me_too_created = ReportMeToo.objects.get_or_create(**keys_data)
    if is_me_too:
        me_too.status = STATUS_PUBLISH
        me_too.save() if me_too.status is not me_too.var_cache['status'] else None
    elif is_me_too is False:
        # do only if is_me_too is REALLY specified with FALSE value.
        me_too.delete()
    elif not is_me_too and me_too_created:
        # only set to STATUS_DELETE if not specify and newly created.
        me_too.delete()
    if me_too.status is not STATUS_PUBLISH:
        me_too = None

    message = message.strip()
    comment_data = None
    if message:
        comment = ReportComment.objects.create(message=message, **keys_data)
        comment_data = ReportCommentSerializer(comment).data

    invalidate_obj(report)

    report = Report.objects.get(id=report.id)

    response_data = {
        'likeId': like and like.id,
        'meTooId': me_too and me_too.id,
        'comment': comment_data,
        'likeCount': report.like_count,
        'meTooCount': report.me_too_count,
        'commentCount': report.comment_count
    }

    type_code = str(int(bool(is_like) and like_created)) + \
                str(int(bool(is_me_too) and me_too_created)) + \
                str(int(bool(message)))

    try:
        notification_type = {
            '111': SUPPORT_LIKE_ME_TOO_COMMENT,
            '011': SUPPORT_ME_TOO_COMMENT,
            '110': SUPPORT_LIKE_ME_TOO,
            '101': SUPPORT_LIKE_COMMENT,
            '100': SUPPORT_LIKE,
            '010': SUPPORT_ME_TOO,
            '001': SUPPORT_COMMENT
        }[type_code]

        Notification.objects.create(
            report=report,
            receive_user=report.created_by,
            created_by=user,
            to=user.username,
            type=notification_type
        )

    except KeyError:
        pass


    # print response_data

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def dashboard_villages(request):
    results = []
    areas = AdministrationArea.objects.all()
    if not request.user.is_staff:
        areas = filter_permitted_administration_areas_and_descendants(request.user, subscribes=True, graph_fields_only=True)

    administration_areas = {}
    for area in areas:
        #if area.is_leaf():
        administration_areas[area.id] = Area(id=area.id, name=area.name, address=area.address, location=area.location)

    body = {
        "query": {
             "range": {
                "date": {
                    "gte": "now-14d",
                    "lt": "now",
                    "boost": 2.0
                }
             },
        },
        "filter": {},
        "aggregations": {
            "area": {
                "terms": {
                    "field": "administrationArea",
                    "size": 0
                },
                "aggregations": {
                    "negative": {
                        "terms": {
                            "field": "negative",
                            "size": 0
                        }
                    }
                }
            }
        }
    }

    current_domain_id = get_current_domain_id(request.user)
    if current_domain_id:
        body['filter'] = {'term': {'domain': current_domain_id}}

    body = json.dumps(body)

    es = get_elasticsearch_instance()

    index = settings.HAYSTACK_CONNECTIONS['default']['INDEX_NAME']
    if not index:
        index = 'haystack'

    reports = es.search(index=index, doc_type="modelresult", body=body, search_type="count")

    for area in reports['aggregations']['area']['buckets']:
        area_id = int(area['key'])
        area_positive = 0
        area_negative = 0
        for flag in area['negative']['buckets']:
            if flag['key'] == 'F':
                area_positive = flag['doc_count']
            elif flag['key'] == 'T':
                area_negative = flag['doc_count']

        if area_id in administration_areas:
            administration_areas[area_id].positive = area_positive
            administration_areas[area_id].negative = area_negative

    serializer = DashboardSerializer(administration_areas.values(), many=True)

    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def reports_summary_by_month(request):
    month = request.QUERY_PARAMS.get('month')
    try:
        month_start = datetime.datetime.strptime(month, '%m/%Y')
        month_end = month_start + relativedelta(months=+1, days=-1)
    except:
        return Response({"month": "Invalid month. Please try again. (eg. 3/2014)"},
                        status=status.HTTP_400_BAD_REQUEST)
    else:
        results = []

        dates_template = []
        for date in Calendar().itermonthdates(month_start.year, month_start.month):
            if date.month == month_start.month:
                dates_template.append({
                    'date': date.strftime('%d-%m-%Y'),
                    'negative': 0,
                    'positive': 0,
                    'total': 0,
                })

        for user in User.objects.all().order_by('first_name', 'last_name'):
            dates = deepcopy(dates_template)
            reports = Report.objects.filter(created_by=user, incident_date__range=(month_start, month_end))
            for report in reports:
                if report.negative:
                    dates[report.incident_date.day-1]['negative'] += 1
                else:
                    dates[report.incident_date.day-1]['positive'] += 1
                dates[report.incident_date.day-1]['total'] += 1

            results.append({
                'fullname': user.get_full_name(),
                'dates': dates,
            })

        return Response(results)


@api_view(['POST', 'PUT'])
def report_protect_update_state(request, report_id, key, state, case, auto_create=False, user=None, extra_info=None):
    # return Response({
    #     'success': True
    # })
    temp_report = Report.default_manager.get(id=report_id)
    current_domain_id = temp_report.domain.id

    if key != settings.UPDATE_REPORT_STATE_KEY:
        raise Http404()

    if user:
        system_user = user
    else:
        from common.functions import get_system_user
        system_user = get_system_user(current_domain_id)

    system_user.domain = temp_report.domain
    system_user.save()
    set_current_user(system_user)

    related_ids = request.GET.getlist('related_ids')
    related_reports = []
    if related_ids:
        related_reports = Report.objects.filter(id__in=related_ids)

    if auto_create and related_reports.count():

        now = timezone.now()

        ref_report = related_reports[0]

        report = Report(
            domain=ref_report.domain,
            created_by=system_user,
            type=ref_report.type,
            administration_area=ref_report.administration_area,
            negative=True,
            guid=str(uuid.uuid1()),
            report_id=0,
            incident_date=now.date(),
            date=now,
            form_data='{}',
            remark='Created by system by accumulated from report id [%s]' % (', '.join([str(r.id) for r in related_reports]))
        )
        report.save()

    else:
        try:
            report = Report.objects.get(domain=temp_report.domain, id=report_id)
        except Report.DoesNotExist:
            raise Http404()
        if report.parent:
            report = report.parent

    try:
        state = ReportState.objects.get(domain=temp_report.domain, code=state, report_type=report.type)
    except ReportState.DoesNotExist:
        raise Http404()
    report.state = state

    try:
        code = re.sub(r'%s$' % current_domain_id, '', case)
        case = CaseDefinition.objects.get(domain=temp_report.domain, code=code, to_state=state)
    except CaseDefinition.DoesNotExist:
        raise Http404()
    case._extra_info = extra_info
    report._state_changed_by_case = case

    report.updated_by = system_user

    report.save()

    return Response({
        'success': True
    })

@api_view(['POST'])
def report_protect_verify_to_suspect_outbreak(request, report_id, key, verified):
    # check if report not already suspect
    report = get_object_or_404(Report, id=report_id)
    if report.state.name == 'Case':
        state_name = "Suspect Outbreak" if verified == "yes" else "False Report"
        case_def_code = "animalVerifiedByReporter" if verified == "yes" else "animalVerifiedToFalseReportByReporter"

        extra_info = request.GET.get('extraInfo')
        suspect_state = get_object_or_404(ReportState, report_type=report.type, name=state_name)
        return report_protect_update_state(request, report_id, key, suspect_state.code, case_def_code, auto_create=False,
                                           user=report.created_by, extra_info=extra_info)
    else:
        return Response({
            'success': True
        })

@api_view(['POST', 'PUT'])
def report_protect_create_with_state(request, key, state, case):

    return report_protect_update_state(request, None, key, state, case, auto_create=True)


class AnimalLaboratoryCauseViewSet(viewsets.ModelViewSet):
    model = AnimalLaboratoryCause
    serializer_class = AnimalLaboratoryCauseSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )


class ReportLaboratoryItemViewSet(viewsets.ModelViewSet):
    model = ReportLaboratoryItem
    serializer_class = ReportLaboratoryItemSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )


class ReportAccomplishmentViewSet(viewsets.ModelViewSet):
    model = ReportAccomplishment
    serializer_class = ReportAccomplishmentSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            report = Report.objects.get(pk=request.DATA['reportId'])
        except Report.DoesNotExist:
            return Response({u'detail': u'Report not found'},
                            status=status.HTTP_403_FORBIDDEN)

        if (has_permission_on_administration_area(user=request.user,
                                                  administration_area=report.administration_area)):

            return super(ReportAccomplishmentViewSet, self).update(request, *args, **kwargs)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def upload_file_to_laboratory(request):
    case = request.POST.get('case')
    file = request.FILES.get('file')
    if not case:
        return Response({"detail": "case is required"},
                    status=status.HTTP_400_BAD_REQUEST)

    if not file:
         return Response({"detail": "file is required"},
                    status=status.HTTP_400_BAD_REQUEST)

    case = get_object_or_404(ReportLaboratoryCase, id=case)
    if file.size <= settings.MAX_ATTACH_FILE_COMMENT_SIZE:
        file_url = upload_to_s3(file)
        if file_url:
            lab_file, created = ReportLaboratoryFile.objects.get_or_create(case=case, name=file.name, file=file_url)
            return Response({
                'id': lab_file.id,
                'name': file.name,
                'file': lab_file.file
            })
        else:
            return Response({"detail": "Cannot upload your file"},
                status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"detail": "Cannot upload file size > 10 MB"},
            status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def delete_file_to_laboratory(request, file_id):
    file = get_object_or_404(ReportLaboratoryFile, id=file_id)
    file.delete()
    return Response({}, status=status.HTTP_204_NO_CONTENT)

