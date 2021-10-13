from django.conf import settings
from django.db import connection
from django.utils import timezone
from datetime import timedelta, date, datetime

from common.functions import publish_line_message
from covid.models import MonitoringReport, DailySummaryByVillage, DailySummary, AuthorityInfo
from notifications.models import Notification, NotificationTemplate


def notify_reporter_when_no_followup_in_n_days():
    today = date.today()
    cut_off_day = today - timedelta(days=settings.COVID_FOLLOWUP_NOTIFICATION_ALARM_DAYS)
    monitors = MonitoringReport.objects.filter(active=True, until__gte=today,
                                               last_updated__lte=cut_off_day)
    for monitor in monitors:
        Notification.objects.create(
            report=monitor.report,
            receive_user=monitor.reporter,
            message=settings.COVID_FOLLOWUP_NOTIFICATION_MESSAGE,
            type=NotificationTemplate.TYPE_NOTIFY_FOLLOW_UP,
            to=monitor.reporter,
            anonymous_send=Notification.LINE_NOTIFICATION_ONLY,
        )


sum_by_risk = '''
SELECT
authority_id,
village_no,
sum(case report_latest_state_code when 'LowRisk' then 1 else 0 end) as low_risk,
sum(case report_latest_state_code when 'MediumRisk' then 1 else 0 end) as medium_risk,
sum(case report_latest_state_code when 'HighRisk' then 1 else 0 end) as high_risk
FROM covid_monitoringreport cmr
where cmr.started_at <= %s
and cmr.until >= %s
group by authority_id, village_no
'''

sum_by_authority = '''
SELECT
authority_id,
count(*) as cnt
from covid_monitoringreport cmr
where cmr.started_at <= %s
and cmr.until >= %s
and report_latest_state_code in ('LowRisk', 'MediumRisk', 'HighRisk')
group by authority_id
'''

risks = ['LowRisk',
         'MediumRisk',
         'HighRisk']


def daily_summarize():
    today = date.today()
    yesterday = today - timedelta(days=1)

    with connection.cursor() as cursor:
        cursor.execute(sum_by_risk, [yesterday, yesterday])
        for row in cursor.fetchall():
            authority_id = row[0]
            village_no = row[1]
            low_risk = row[2]
            medium_risk = row[3]
            high_risk = row[4]
            DailySummaryByVillage.objects.update_or_create(
                authority_id=authority_id,
                date=yesterday,
                village_no=village_no,
                defaults={
                    "low_risk": low_risk,
                    "medium_risk": medium_risk,
                    "high_risk": high_risk
                }
            )
        cursor.execute(sum_by_authority, [yesterday, yesterday])
        for row in cursor.fetchall():
            authority_id = row[0]
            qty_ongoing_monitoring = row[1]
            qty_new_monitoring = MonitoringReport.objects.filter(authority_id=authority_id, started_at=yesterday,
                                                                 report_latest_state_code__in=risks).count()
            qty_new_case = MonitoringReport.objects.filter(authority_id=authority_id,
                                                           started_at=yesterday,
                                                           report_latest_state_code="ConfirmedCase"
                                                           ).count()
            qty_acc_finished = MonitoringReport.objects.filter(authority_id=authority_id,
                                                               until__lt=yesterday,
                                                               report_latest_state_code__in=risks).count()
            DailySummary.objects.update_or_create(
                authority_id=authority_id,
                date=yesterday,
                defaults={
                    "qty_new_case": qty_new_case,
                    "qty_ongoing_monitoring": qty_ongoing_monitoring,
                    "qty_new_monitoring": qty_new_monitoring,
                    "qty_acc_finished": qty_acc_finished
                }
            )


def daily_notify_authority():
    today = date.today()
    yesterday = today - timedelta(days=1)
    yesterday_str = datetime.strftime(yesterday, "%Y-%m-%d")
    for authorityInfo in AuthorityInfo.objects.all():
        authority = authorityInfo.authority
        line_token = authorityInfo.line_notify_token
        if line_token is not None:
            msg = 'สรุปการเฝ้าระวังโรคติดเชื้อโควิด-19 วันที่ %s link: https://api.cmonehealth.org/covid/summary/%s?date=%s' % (
                yesterday_str, authority.id, yesterday_str)
            publish_line_message(msg, line_token)
