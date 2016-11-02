import calendar

from django.conf import settings
from django.utils import timezone
from django.utils.log import getLogger
from django_redis import get_redis_connection

from accounts.models import Authority, Configuration
from common.models import Domain


def get_public_feed_key(administration_area):
    """Return public feed key for specific authority id"""
    pattern = "podd:domain:%d:feed:public:administration_area:%d"
    return pattern % (administration_area.domain.pk, int(administration_area.pk))


def warm_cache_public_feed(logger=None):
    """
    Warm cache for all administration area for public authority

    :param logger
    """
    if not logger:
        logger = getLogger()

    domains = Domain.objects.all()
    for domain in domains:
        try:
            authority = Authority.objects.get(name="public_%d" % domain.id)
            for administration_area in authority.administration_areas.all():
                administration_area.warm_cache_public_feed()
                logger.info("Done warm cache on public feed for authority:%d / area:%d" % (authority.id,
                                                                                           administration_area.id))
        except Authority.DoesNotExist:
            pass


def purge_all_expired_cache():
    """
    Purge all public feed expired cached items.
    """
    try:
        days = int(Configuration.objects.get(system='web.dodd.configuration', key='n_last_days').value)
    except Configuration.DoesNotExist:
        days = 90

    ttl = getattr(settings, 'FEED_CACHE_PERIOD_LIMIT', timezone.timedelta(days=days))
    limit = timezone.now() - ttl
    limit = calendar.timegm(limit.utctimetuple())
    redis = get_redis_connection()
    ''':type redis: redis.StrictRedis'''

    domains = Domain.objects.all()
    for domain in domains:
        try:
            authority = Authority.objects.get(name="public_%d" % domain.id)
            for administration_area in authority.administration_areas.all():
                feed_key = get_public_feed_key(administration_area)
                redis.zremrangebyscore(feed_key, '-INF', limit)

        except Authority.DoesNotExist:
            pass


def get_summary_from_feed(administration_areas, length=3):

    from django.db.models import Count
    from reports.models import Report, AdministrationArea, ReportTypeCategory

    result = {}

    redis = get_redis_connection()
    report_id_list = []

    for administration_area in administration_areas:
        public_feed_key = get_public_feed_key(administration_area)

        ''':type redis: redis.client.StrictRedis'''
        _tmp_report_id_list = redis.zrange(public_feed_key, 0, -1)
        if _tmp_report_id_list:
            for report_id in _tmp_report_id_list:
                report_id_list.append(report_id)

    report_items_list = Report.objects.filter(id__in=report_id_list)
    result['report_count'] = report_items_list.count()

    support_count = report_items_list.extra(select={'support_count': 'SUM(like_count + me_too_count)'})\
                                .values('support_count').order_by('support_count')
    if support_count:
        support_count = support_count[0]['support_count']
    else:
        support_count = 0

    result['support_count'] = support_count
    report_types = report_items_list.values('type').annotate(total=Count('type')).order_by('-total')

    category_count = []
    for category in ReportTypeCategory.objects.all():
        category_report_types = category.report_type_category.all().values_list('id', flat=True)
        answer = 0
        for report_type in report_types:
            if report_type['type'] in category_report_types:
                answer += report_type['total']

        category_count.append({
            'name': category.name,
            'code': category.code,
            'count': answer
        })

    result['category_count'] = category_count

    hot_report_types = []
    temp_hot_report_types = report_items_list.values('type__name').annotate(count=Count('type')).order_by('-count')[:length]
    for temp in temp_hot_report_types:
        hot_report_types.append({
            'type': temp['type__name'],
            'count': temp['count']
        })

    result['hot_report_types'] = hot_report_types
    return result