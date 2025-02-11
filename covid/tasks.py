# -*- encoding: utf-8 -*-
import json
import urllib2

from django.conf import settings
from django.db import connection
from datetime import timedelta, date, datetime

from django.db.models import Count

from accounts.models import User
from common.functions import publish_line_message
from covid.models import MonitoringReport, DailySummaryByVillage, DailySummary, AuthorityInfo
from podd.celery import app


def push_line_message(line_id):
    url = settings.LINE_MESSAGING_API_ENDPOINT
    message = settings.COVID_FOLLOWUP_NOTIFICATION_MESSAGE
    label = settings.LINE_FOLLOWUP_LABEL
    payload = {
        'to': line_id,
        'messages': [
            {
                "type": "template",
                "altText": label,
                "template": {
                    "type": "buttons",
                    "text": message,
                    "actions": [
                        {
                            "type": "uri",
                            "label": label,
                            "uri": settings.LINE_LIFF_COVID_MONITORING_URL
                        }
                    ]
                }
            }
        ]
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % (settings.LINE_ACCESS_TOKEN,)
    }
    req = urllib2.Request(url, data=json.dumps(payload), headers=headers)
    response = urllib2.urlopen(req)
    if response.code != 200:
        print("error sending line message code: %s, msg: %s" % (response.code, response.msg))


@app.task
def notify_reporter_when_no_followup_in_n_days():
    today = date.today()
    cut_off_day = today - timedelta(days=settings.COVID_FOLLOWUP_NOTIFICATION_ALARM_DAYS)
    monitors = MonitoringReport.objects.filter(active=True, until__gte=today, last_updated__lte=cut_off_day).values(
        'reporter_id').annotate(total=Count('reporter_id'))
    for monitor in monitors:
        reporter_id = monitor['reporter_id']
        number_of_unfollowup = monitor['total']
        u = User.default_manager.get(pk=reporter_id)
        if u.line_id:
            # push message to line notification
            push_line_message(u.line_id)


sum_by_risk = '''
SELECT
authority_id,
village_no,
sum(case report_latest_state_code when 'LowRisk' then 1 else 0 end) as low_risk,
sum(case report_latest_state_code when 'MediumRisk' then 1 else 0 end) as medium_risk,
sum(case report_latest_state_code when 'HighRisk' then 1 else 0 end) as high_risk,
sum(case report_latest_state_code when 'ConfirmedCase' then 1 else 0 end) as confirmed
FROM covid_monitoringreport cmr
where cmr.started_at <= %s
and cmr.until >= %s
group by authority_id, village_no
'''

sum_confirmed_14_by_village = '''
SELECT
authority_id,
village_no,
sum(confirmed) as confirmed
FROM covid_dailysummarybyvillage
where date between %s and %s
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


@app.task
def daily_summarize():
    today = date.today()
    yesterday = today - timedelta(days=1)
    back_14 = yesterday - timedelta(days=14)

    with connection.cursor() as cursor:
        authority_confirmed = {}
        cursor.execute(sum_confirmed_14_by_village, [back_14, yesterday])
        for row in cursor.fetchall():
            authority_id = row[0]
            village_no = row[1]
            confirmed = row[2]
            authority_confirmed[(authority_id, village_no)] = confirmed

        cursor.execute(sum_by_risk, [yesterday, yesterday])
        for row in cursor.fetchall():
            authority_id = row[0]
            village_no = row[1]
            low_risk = row[2]
            medium_risk = row[3]
            high_risk = row[4]
            confirmed = row[5]
            confirmed_found_in_14 = 0
            if (authority_id, village_no) in authority_confirmed:
                confirmed_found_in_14 = authority_confirmed[(authority_id, village_no)]
            (obj, flag) = DailySummaryByVillage.objects.update_or_create(
                authority_id=authority_id,
                date=yesterday,
                village_no=village_no,
                defaults={
                    "low_risk": low_risk,
                    "medium_risk": medium_risk,
                    "high_risk": high_risk,
                    "confirmed": confirmed,
                    "confirmed_found_in_14": confirmed_found_in_14
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


@app.task
def daily_notify_authority():
    today = date.today()
    yesterday = today - timedelta(days=1)
    yesterday_str = datetime.strftime(yesterday, "%Y-%m-%d")
    for authorityInfo in AuthorityInfo.objects.all():
        authority = authorityInfo.authority
        line_token = authorityInfo.line_notify_token
        cnt = DailySummary.objects.filter(date=yesterday).count()
        if line_token is not None and cnt > 0:
            msg = 'สรุปการเฝ้าระวังโรคติดเชื้อโควิด-19 วันที่ %s link: https://api.cmonehealth.org/covid/summary/%s/?date=%s' % (
                yesterday_str, authority.id, yesterday_str)
            publish_line_message(msg, line_token, authority.id)
