from datetime import timedelta, date

import pytz
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from covid.models import MonitoringReport, DailySummary, DailySummaryByVillage
from covid.serializers import MonitoringReportSerializer, DailySummaryByVillageSerializer, DailySummarySerializer

from datetime import datetime


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def list_monitoring(request):
    all = request.GET.get('all')
    timezone = pytz.timezone("Asia/Bangkok")
    today = date.today()
    user = request.user
    reports = MonitoringReport.objects.filter(
        active=True,
        until__gte=today,
    ).prefetch_related("report")
    if all:
        reports = reports.filter(reporter_id=user.id)
    else:
        reports = reports.filter(authority__in=user.authority_users.all())

    serializer = MonitoringReportSerializer(reports, many=True)
    return Response(serializer.data)


def daily_summary(request, authority_id):
    date_str = request.GET.get('date')
    parsed_date = datetime.strptime(date_str, "%Y-%m-%d")

    daily_summary = DailySummary.objects.filter(authority_id=authority_id, date=parsed_date)
    daily_summary_by_village = DailySummaryByVillage.objects.filter(authority_id=authority_id, date=parsed_date)

    return render(request, 'covid/daily_summary.html', {
        "daily_summary": daily_summary,
        "daily_summary_by_village": daily_summary_by_village
    })