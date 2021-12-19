from datetime import timedelta, date

import pytz
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Authority
from common.utils import thai_strftime
from covid.models import MonitoringReport, DailySummary, DailySummaryByVillage
from covid.serializers import MonitoringReportSerializer, DailySummaryByVillageSerializer, DailySummarySerializer

from datetime import datetime


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def list_monitoring(request):
    all_flag = request.GET.get('all')
    timezone = pytz.timezone("Asia/Bangkok")
    today = date.today()
    user = request.user
    reports = MonitoringReport.objects.filter(
        active=True,
        until__gte=today,
    ).prefetch_related("report")
    if all_flag:
        reports = reports.filter(authority__in=user.authority_users.all())
    else:
        reports = reports.filter(reporter_id=user.id)

    serializer = MonitoringReportSerializer(reports, many=True)
    return Response(serializer.data)


def daily_summary(request, authority_id):
    date_str = request.GET.get('date')
    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    class EmptyDailySummary:
        def __init__(self):
            self.qty_new_case = 0
            self.qty_new_monitoring = 0
            self.qty_ongoing_monitoring = 0
            self.qty_acc_finished = 0
            self.qty_total = 0
    try:
        ds = DailySummary.objects.get(authority_id=authority_id, date=parsed_date)
        dsbv = DailySummaryByVillage.objects.filter(authority_id=authority_id, date=parsed_date).order_by('village_no')
        authority = Authority.default_manager.get(pk=authority_id)

        total_low_risk = 0
        total_medium_risk = 0
        total_high_risk = 0
        total_total = 0
        for village in dsbv:
            total_low_risk += village.low_risk
            total_medium_risk += village.medium_risk
            total_high_risk += village.high_risk
            total_total += village.total

        return render(request, 'covid/daily_summary.html', {
            "daily_summary": ds,
            "daily_summary_by_village": dsbv,
            "date": parsed_date,
            "th_date": thai_strftime(parsed_date),
            "authority": authority,
            "total_low_risk": total_low_risk,
            "total_medium_risk": total_medium_risk,
            "total_high_risk": total_high_risk,
            "total_total": total_total
        })
    except DailySummary.DoesNotExist:
        return render(request, 'covid/daily_summary.html', {
            "daily_summary": EmptyDailySummary(),
            "daily_summary_by_village": [],
            "date": parsed_date,
            "th_date": thai_strftime(parsed_date),
            "authority": Authority.default_manager.get(pk=authority_id),
            "total_low_risk": 0,
            "total_medium_risk": 0,
            "total_high_risk": 0,
            "total_total": 0
        })
