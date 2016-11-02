# -*- encoding: utf-8 -*-

import datetime
import json
from urlparse import urlparse

from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point, GEOSGeometry
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from common.decorators import superuser_required
from reports.forms import ReportInvestigationForm
from reports.models import AdministrationArea, Report, ReportImage
from reports.serializers import ReportSerializer


def search_nearby_area(request):
    query = request.GET.get('query')
    latitude = request.GET.get('lat')
    longitude = request.GET.get('log')
    
    areas = []
    if query and latitude and longitude:
        query_point = GEOSGeometry('SRID=4326;POINT(%(longitude)s %(latitude)s)'% {
                'latitude': latitude,
                'longitude': longitude
            })

        administration_areas = AdministrationArea.objects.order_by('id')
        for administration_area in administration_areas:
            if administration_area.is_leaf():
                try:
                    parent_name = administration_area.get_parent().name
                except:
                    parent_name = ''

                data_point = administration_area.location
                distance = query_point.distance(data_point) * 1000

                area = {
                    'parent_name': parent_name,
                    'name': administration_area.name,
                    'address': administration_area.address,
                    'lat': administration_area.location[1],
                    'log': administration_area.location[0],
                    'distance': distance
                }
                areas.append(area)
        areas = sorted(areas, key=lambda k: k['distance'])
        if len(areas) > 10:
            areas = areas[0:10]
    context = {
        'areas': areas,
        'query': query,
    }
    return render(request, 'area/search_nearby_area.html', context)


def get_feed_icon(code, size=''):

    if code not in ['human', 'animal', 'environment', 'podd']:
        code = 'podd'

    return '/static/images/share/ico-%s.imageset/ico-%s%s.png' % (code, code, size)


def _report_share(request, report):

    code = 'podd'
    if report.is_public:
        code = report.type.category.code

    feed_icon = get_feed_icon(code)

    feed_color_map = {
        "human": "#F4A60C",
        "animal": "#CF6221",
        "environment": "#96B220",
        "podd": "#A079B5"
    }
    feed_color = feed_color_map.get(code) or feed_color_map['podd']

    report_data = ReportSerializer(report).data

    avatar = report_data[
                 'createdByThumbnailUrl'] or '/static/images/share/default-image-profile.imageset/default-image-profile.png'
    display_name = report_data['createdByName'].strip() or u'ไม่ระบุตัวตน'
    try:
        display_name = display_name.decode('utf-8')
    except:
        pass

    image = None
    thumbnail = None
    image_list = ReportImage.default_manager.filter(report=report)
    if image_list.count():
        image = image_list[0].image_url
        thumbnail = image_list[0].thumbnail_url

    if not image:
        image = get_feed_icon(code, '@3x')

    if not thumbnail:
        thumbnail = get_feed_icon(code, '@3x')

    image = request.build_absolute_uri(image)

    DISPLAY_NAME_MAX_LENGTH = 16
    DISPLAY_NAME_SUFFIX = '...'

    if len(display_name) > DISPLAY_NAME_MAX_LENGTH:
        display_name = display_name[0: (DISPLAY_NAME_MAX_LENGTH - len(DISPLAY_NAME_SUFFIX))]



    # Prepare report
    report_data['feed_header_color'] = feed_color
    report_data['feed_icon'] = feed_icon
    report_data['avatar'] = avatar
    report_data['image'] = image
    report_data['thumbnail'] = thumbnail
    report_data['display_name'] = display_name
    report_data['created_at'] = report.created_at

    return report_data


def report_share(request, report_id=None):

    base = '/static/images/share/'

    comment_icon = base + 'ico-comment.imageset/ico-comment.png'
    share_icon = base + 'ico-share.imageset/ico-share.png'

    favorite_icon = base + 'ic_favorite_black_24dp/web/ic_favorite_black_24dp.png'
    room_icon = base + 'ic_room_black_24dp/web/ic_room_black_24dp.png'
    thumb_up_icon = base + 'ic_thumb_up_black_24dp/web/ic_thumb_up_black_24dp.png'

    playstore_icon = base + 'playstore.png'
    appstore_icon = base + 'appstore.png'

    iphone_bg = base + 'iphone5.png'

    base_url = request.build_absolute_uri('/')
    o = urlparse(base_url)


    report_list = []

    if report_id:
        try:
            report = Report.default_manager.get(guid=report_id)
        except Report.DoesNotExist:
            try:
                report = Report.default_manager.get(id=report_id)
            except Report.DoesNotExist:
                raise Http404()

        report_data = _report_share(request, report)
        report_list.append(report_data)

        createdByName = report_data['createdByName']
        try:
            createdByName = createdByName.decode('utf-8')
        except:
            pass

        reportTypeName = report_data['reportTypeName']
        try:
            reportTypeName = reportTypeName.decode('utf-8')
        except:
            pass

        title = u'รายงานของ %s เรื่อง %s บน ดูดีดี by PODD แอปพลิเคชั่นดูแลชุมชน' % (
            createdByName,
            reportTypeName
        )
        thumbnail = report_data['thumbnail']

    else:
        for report in Report.default_manager.filter((Q(curated_in__isnull=False) | Q(is_public=True)) & Q(images__isnull=False)).order_by('-created_at')[0:20]:
            report_data = _report_share(request, report)
            report_list.append(report_data)

        title = u'ดูดีดี by PODD แอปพลิเคชั่นดูแลชุมชน'
        thumbnail = 'https://s3-ap-southeast-1.amazonaws.com/podd/mail-template/logo@3x.png'


    return render(request, 'report/share.html', {
        # Global
        'comment_icon': comment_icon,
        'share_icon': share_icon,
        'favorite_icon': favorite_icon,
        'room_icon': room_icon,
        'thumb_up_icon': thumb_up_icon,

        'playstore_icon': playstore_icon,
        'appstore_icon': appstore_icon,
        'iphone_bg': iphone_bg,

        'base_url': base_url,
        'current_url': request.build_absolute_uri(),
        'site_name': o.netloc,

        # Meta
        'title': title,
        'description': u'สุขภาพชุมชนของเราเป็นสิ่งสำคัญ คุณก็เป็นส่วนหนึ่งในการร่วมดูแลได้ ร่วมด้วยช่วยกันรายงาน บอกปัญหาให้ทุกคนรู้ เพียงถ่ายรูป และส่งรายละเอียดผ่านแอปพลิเคชั่น ปัญหาที่คุณพบอาจจะมีเพื่อนคนอื่นประสบเหมือนกันอยู่ มาพูดคุยและช่วยเหลือกัน',
        'thumbnail': thumbnail,

        # Report
        'report_list': report_list,

    })
