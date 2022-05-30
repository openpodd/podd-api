# -*- encoding: utf-8 -*-
from datetime import datetime

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json

from civic.models import LetterFieldConfiguration
from civic.utils import thai_strftime
from reports.models import Report, ReportAccomplishment
from reports.paginations import PaginatedReportSerializer


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def list_civic_report(request, status):
    page_size = request.QUERY_PARAMS.get('page_size') or 20
    page = request.QUERY_PARAMS.get('page') or 1
    user = request.user
    authority = user.get_my_authority()
    queryset = Report.objects.filter(administration_area__authority=authority,
                                     type__code=settings.CIVIC_REPORT_TYPE_CODE,
                                     state__code=status)
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
    letter_config_query = LetterFieldConfiguration.objects.filter(code='civic', authority=report.administration_area.authority)
    if letter_config_query.exists():
        letter_config = letter_config_query.first()

    date_fmt = "%-d %B %Y"
    context = {
        'show_html': request.GET.get('show_html', ''),
        'letter_date': thai_strftime(datetime.today(), thaidigit=True),
        'organization_address1': letter_config.header_address1,
        'organization_address2': letter_config.header_address2,
        'organization_name': authority.name,
        'report_topic': form["incident"],
        'report_to': reporter.name,
        'question': form["incident"],
        'report_id': report.id,
        'report_date': thai_strftime(report.date, thaidigit=True),
        'report_description':  form["detail"] if "detail" in form else "",
        'signature_name': letter_config.sign_name,
        'signature_position1': letter_config.sign_position1,
        'signature_position2': letter_config.sign_position2,
        'department_name': letter_config.footer_contact_line1,
        'department_contact1': letter_config.footer_contact_line2,
        'department_contact2': letter_config.footer_contact_line3,
    }
    return render(request, 'civic/letter.html', context)


def success_story(request):
    query = ReportAccomplishment.objects.filter(report__type__code=settings.CIVIC_REPORT_TYPE_CODE, public_showcase=True)
    authority_id = request.GET.get('authority_id', None)
    if authority_id:
        query = query.filter(report__administration_area__authority_id=authority_id)
    query = query.order_by("-report__date")[:10]

    data = [{
        "image_url": row.get_first_image_thumbnail_url(),
        "title": row.title,
        "description": row.description
    } for row in query]

    return render(request, 'civic/success_report.html', {
        'data': data
    })