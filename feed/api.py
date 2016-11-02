# -*- encoding: utf-8 -*-

import calendar

from django.core.paginator import Paginator, EmptyPage
from django.utils.dateparse import parse_datetime
from django_redis import get_redis_connection

from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Authority
from feed.functions import get_public_feed_key, get_summary_from_feed
from reports.models import Report, AdministrationArea
from reports.paginations import PaginatedReportSerializer
from reports.serializers import AdministrationAreaDetailSerializer

@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def items_list(request):
    """
    Response list of public report by administration area id

    :param request
    """
    # Build redis sorted set query.
    query_params = request.QUERY_PARAMS
    administration_area_id = query_params.get('administrationArea')

    if not administration_area_id:
        return Response("administrationArea is required", 400)

    try:
        administration_areas = [AdministrationArea.objects.get(id=administration_area_id)]
    except AdministrationArea.DoesNotExist:

        # TO DO: Filter จังหวัดเชียงใหม่
        if administration_area_id == '-1':
            try:
                authority = Authority.objects.get(name="public_%d" % request.user.domain.id)
                administration_areas = authority.administration_areas.all()
                administration_areas = administration_areas.filter(mpoly__isnull=False).order_by('id')

            except Authority.DoesNotExist:
                return Response("administrationArea not found", 404)
        else:
            return Response("administrationArea not found", 404)

    max_score = query_params.get('createdAt__lt', '+INF')
    min_score = query_params.get('createdAt__gt', '-INF')
    if max_score is not '+INF':
        max_score = parse_datetime(max_score)
        max_score = calendar.timegm(max_score.utctimetuple())
    if min_score is not '-INF':
        min_score = parse_datetime(min_score)
        min_score = calendar.timegm(min_score.utctimetuple())

    page_size = min(100, int(query_params.get('page_size', 20)))  # limit page_size to not more then 100
    redis = get_redis_connection()
    report_id_list = []
    report_count = 0
    for administration_area in administration_areas:
        public_feed_key = get_public_feed_key(administration_area)

        ''':type redis: redis.client.StrictRedis'''
        _tmp_report_id_list = redis.zrevrangebyscore(public_feed_key, max_score, min_score)
        if _tmp_report_id_list:
            for report_id in _tmp_report_id_list:
                report_id_list.append(report_id)
            report_count = report_count + redis.zcard(public_feed_key)

        # Delete because administration all area in public.
        # Get report object from database (because of report view for each user is not the same).
        # for report_id in report_id_list:
        #     try:
        #         report_item = Report.objects.get(id=report_id)
        #         report_items_list.append(report_item)
        #     except Report.DoesNotExist:
        #         pass

    report_items_list = []
    for item in Report.objects.filter(id__in=report_id_list).order_by('-created_at'):

        # for podd reporter privacy
        if not item.is_public:
            item.is_anonymous = True
            item.comment_count = item.comments.filter(created_by__is_public=True).count()

        report_items_list.append(item)

    # Make pager, just a placeholder pager. No value can be used for client.
    paginator = Paginator(report_items_list, page_size)
    page = request.QUERY_PARAMS.get('page', 1)

    data = {}
    try:
        feed_items = paginator.page(page)
    except EmptyPage:
        data = {
                'count': 0,
                'next': None,
                'previous': None,
                'results': []
        }
    else:
        serializer = PaginatedReportSerializer(feed_items)
        data = serializer.data
        data['count'] = len(report_items_list)

    return Response(data)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def items_list_mine(request):
    # Build query.
    query_params = request.QUERY_PARAMS
    page_size = min(100, int(query_params.get('page_size', 20)))  # limit page_size to not more then 100
    created_at__gt = query_params.get('createdAt__gt')
    created_at__lt = query_params.get('createdAt__lt')

    report_items_list = Report.objects.filter(
        is_public=True,
        created_by=request.user
    )

    if created_at__gt:
        report_items_list = report_items_list.filter(created_at__gt=created_at__gt)
    if created_at__lt:
        report_items_list = report_items_list.filter(created_at__lt=created_at__lt)

    report_items_list = report_items_list.order_by('-created_at')

    # Make pager, just a placeholder pager. No value can be used for client.
    paginator = Paginator(report_items_list, page_size)
    page = request.QUERY_PARAMS.get('page', 1)

    data = {}
    try:
        feed_items = paginator.page(page)
    except EmptyPage:
        data = {
                'count': 0,
                'next': None,
                'previous': None,
                'results': []
        }
    else:
        serializer = PaginatedReportSerializer(feed_items)
        data = serializer.data
    return Response(data)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def get_area_from_feed(request, pk):

    query_params = request.QUERY_PARAMS
    administration_area_id = pk

    try:
        administration_area = AdministrationArea.objects.get(id=administration_area_id)
        administration_areas = [administration_area]
    except AdministrationArea.DoesNotExist:

        # TO DO: Filter จังหวัดเชียงใหม่
        if administration_area_id == '-1':
            try:
                authority = Authority.objects.get(name="public_%d" % request.user.domain.id)
                administration_areas = authority.administration_areas.all()
                administration_areas = administration_areas.filter(mpoly__isnull=False).order_by('id')
                administration_area = AdministrationArea(id=-1,
                                                         name=u"จังหวัดเชียงใหม่",
                                                         code="public_%d" % request.user.domain.id)

            except Authority.DoesNotExist:
                return Response("administrationArea not found", 404)
        else:
            return Response("administrationArea not found", 404)

    summary = get_summary_from_feed(administration_areas)
    administration_area.get_last_n_days_report_count = summary['report_count'] if 'report_count' in summary else 0
    administration_area.get_last_n_days_support_count = summary['support_count'] if 'support_count' in summary else 0
    administration_area.get_last_n_days_category_count = summary['category_count'] if 'category_count' in summary else []
    administration_area.get_last_n_days_hot_report_types = summary['hot_report_types'] if 'hot_report_types' in summary else []

    if not request.GET.get('withMpoly'):
        administration_area.mpoly = None

    serializer = AdministrationAreaDetailSerializer(administration_area)

    return Response(serializer.data)
