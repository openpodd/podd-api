# -*- encoding: utf-8 -*-
import json

from datetime import datetime, timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponseNotFound
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from civic.models import LetterFieldConfiguration
from civic.utils import thai_strftime, utc_to_local
from common.constants import STATUS_PUBLISH
from logs.models import LogAction, LogItem
from reports.models import Report, ReportAccomplishment, ReportState
from reports.paginations import PaginatedReportSerializer


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def list_civic_report(request, status):
    try:
        tz = int(request.QUERY_PARAMS.get('tz'))
    except:
        tz = 0
    page_size = request.QUERY_PARAMS.get('page_size') or 20
    page = request.QUERY_PARAMS.get('page') or 1
    include_test_flag = request.QUERY_PARAMS.get('includeTestFlag') or None
    user = request.user
    date_from = request.QUERY_PARAMS.get('dateFrom') or None
    date_to = request.QUERY_PARAMS.get('dateTo') or None
    authority = user.get_my_authority()
    queryset = Report.objects.filter(administration_area__authority=authority,
                                     type__code=settings.CIVIC_REPORT_TYPE_CODE,
                                     state__code=status)
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d') + timedelta(hours=-tz)
        queryset = queryset.filter(date__gte=date_from)

    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(hours=-tz)
        queryset = queryset.filter(date__lte=date_to)

    if not include_test_flag:
        queryset = queryset.filter(negative=True)

    pagination_serializer_class = PaginatedReportSerializer
    paginator = Paginator(queryset, page_size)
    reports = paginator.page(page)
    serializer = pagination_serializer_class(reports)
    return Response(serializer.data)


def letter(request, report_id):
    report = Report.objects.get(pk=report_id)
    reporter = report.created_by
    authority = report.administration_area.authority
    form = json.loads(report.form_data)
    letter_config_query = LetterFieldConfiguration.objects.filter(code='civic',
                                                                  authority=report.administration_area.authority)
    if letter_config_query.exists():
        letter_config = letter_config_query.first()

    date_fmt = "%-d %B %Y"
    context = {
        'show_html': request.GET.get('show_html', ''),
        'letter_date': thai_strftime(datetime.today(), thaidigit=True),
        'organization_address1': letter_config.header_address1,
        'organization_address2': letter_config.header_address2,
        'organization_name': authority.name,
        'report_topic': form["topic"],
        'report_to': reporter.name,
        'question': form["topic"],
        'report_id': report.id,
        'report_date': thai_strftime(report.date, thaidigit=True),
        'report_description': form["detail"] if "detail" in form else "",
        'signature_name': letter_config.sign_name,
        'signature_position1': letter_config.sign_position1,
        'signature_position2': letter_config.sign_position2,
        'department_name': letter_config.footer_contact_line1,
        'department_contact1': letter_config.footer_contact_line2,
        'department_contact2': letter_config.footer_contact_line3,
    }
    return render(request, 'civic/letter.html', context)


def accomplishments(request):
    query = ReportAccomplishment.objects.filter(report__type__code=settings.CIVIC_REPORT_TYPE_CODE,
                                                public_showcase=True)
    authority_id = request.GET.get('authority_id', None)
    if authority_id:
        query = query.filter(report__administration_area__authority_id=authority_id)
    query = query.order_by("-report__date")[:10]

    data = [{
        "image_url": row.get_first_image_thumbnail_url(),
        "title": row.title,
        "description": row.description
    } for row in query]

    return render(request, 'civic/showcase.html', {
        'data': data
    })


def get_first_two_image(report):
    imgs = report.images.all()[:2]
    img1 = None
    img2 = None
    if len(imgs) > 0:
        img1 = imgs[0].image_url
        if len(imgs) > 1:
            img2 = imgs[1].image_url
    return [img1, img2]


def get_report_location(report):
    if report.report_location:
        latitude = report.report_location.y
        longitude = report.report_location.x
    else:
        latitude = report.administration_location.y
        longitude = report.administration_location.x

    return [latitude, longitude]


def display_civic_new_report(request, report_id):
    report = Report.objects.get(pk=report_id)
    authority = report.administration_area.authority
    if report.type.code != settings.CIVIC_REPORT_TYPE_CODE:
        return HttpResponseNotFound("report not found")

    [img1, img2] = get_first_two_image(report)
    [latitude, longitude] = get_report_location(report)

    return render(request, 'civic/report.html', {
        "map_api_key": settings.GOOGLE_STATIC_MAP_API_KEY,
        "report_id": report.id,
        "report_date": thai_strftime(datetime=utc_to_local(report.date), fmt="%A %-d %B %Y เวลา %H:%M", thaidigit=False),
        "incident_date": thai_strftime(datetime=report.incident_date, fmt="%A %-d %B %Y", thaidigit=False),
        "report_type_name": report.type.name,
        "authority_name": authority.name,
        "description": report.rendered_form_data,
        "image1_url": img1,
        "image2_url": img2,
        "latitude": latitude,
        "longitude": longitude,
        "area_name": report.administration_area.name,
        "report_by": report.created_by.name,
        "phone": report.created_by.telephone,
    })


def display_civic_success_report(request, report_id):
    report = Report.objects.get(pk=report_id)
    if report.type.code != settings.CIVIC_REPORT_TYPE_CODE:
        return HttpResponseNotFound("report not found")

    [img1, img2] = get_first_two_image(report)
    [latitude, longitude] = get_report_location(report)

    log_action = LogAction.objects.get(name='REPORT_STATE_CHANGE')
    history_queryset = LogItem.objects.filter(action=log_action, object_id1=report.id).order_by('-created_at')

    verify_date = None
    finished_date = None
    for log_item in history_queryset:
        state = ReportState.objects.get(id=log_item.object_id2)
        if state.code == 'case':
            verify_date = log_item.created_at
        if state.code == 'finish':
            finished_date = log_item.created_at

    comments = [{
        "body": comment.message,
        "date": thai_strftime(datetime=comment.created_at, fmt="%A %-d %B %Y เวลา %H:%M"),
    } for comment in report.comments.filter(status = STATUS_PUBLISH, state = None).order_by('created_at')]

    accomplishment = report.accomplishments.first()

    years = finished_date.year - report.date.year
    months = finished_date.month - report.date.month
    minutes = finished_date.minute - report.date.minute
    days = finished_date.day - report.date.day
    hours = finished_date.hour - report.date.hour
    minutes = finished_date.minute - report.date.minute
    total_time = ""
    if (years):
        total_time += '%d ปี %d เดือน %d วัน %d ชั่วโมง %d นาที' % (
            years, months, days, hours, minutes)
    elif (months):
        total_time += '%d เดือน %d วัน %d ชั่วโมง %d นาที' % (
            months, days, hours, minutes)
    elif (days):
        total_time += '%d วัน %d ชั่วโมง %d นาที' % (days, hours, minutes)
    elif (hours):
        total_time += '%d ชั่วโมง %d นาที' % (hours, minutes)
    else:
        total_time += '%d นาที' % (minutes)

    return render(request, 'civic/success.html', {
        "map_api_key": settings.GOOGLE_STATIC_MAP_API_KEY,
        "report_id": report.id,
        "report_type_name": report.type.name,
        "description": report.rendered_form_data,
        "image1_url": img1,
        "image2_url": img2,
        "latitude": latitude,
        "longitude": longitude,
        "area_name": report.administration_area.name,
        "report_date": thai_strftime(datetime=utc_to_local(report.date), fmt="%A %-d %B %Y เวลา %H:%M", thaidigit=False),
        "incident_date": thai_strftime(datetime=report.incident_date, fmt="%A %-d %B %Y", thaidigit=False),
        "finished_date": thai_strftime(datetime=utc_to_local(finished_date), fmt="%A %-d %B %Y เวลา %H:%M",
                                       thaidigit=False) if finished_date else None,
        "verify_date": thai_strftime(datetime=utc_to_local(verify_date), fmt="%A %-d %B %Y เวลา %H:%M",
                                     thaidigit=False) if verify_date else None,
        "comments": comments,
        "accomplish_title": accomplishment.title if accomplishment else None,
        "accomplish_description": accomplishment.description if accomplishment else None,
        "total_time": total_time
    })
