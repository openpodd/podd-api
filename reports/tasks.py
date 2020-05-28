# -*- encoding: utf-8 -*-

from __future__ import absolute_import

import StringIO
import json
import re
import urllib2

import requests
from PIL import Image
from celery.utils.log import get_task_logger
from django.conf import settings
from django.template import Template, Context

from accounts.models import (Authority)
from common.constants import (PRIORITY_IGNORE)
from common.decorators import domain_celery_task
from common.functions import (get_exif_data, get_lat_lon, get_administration_area_and_ancestors_ids,
                              put_data_to_spreadsheet, has_permission_area_in_authorities,
                              put_event_to_calendar,
                              delete_calendar_events, safe_str)
from flags.functions import create_flag_comment
from flags.serializers import FlagSerializer
from logs.models import LogItem
from podd.celery import app, DomainTask
from reports.models import (ReportImage, SpreadsheetResponse, GoogleCalendarResponse,
                            GoogleCalendarResponseEvent)
from reports.pub_tasks import publish_report_flag
from reports.serializers import ReportSerializer


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def extract_image_gps(report_image_guid):
    '''
    Extract location data from image if possible then save it back to DB.
    '''
    print "Extracting GPS data from image : %s" % report_image_guid
    report_image = ReportImage.objects.get(guid=report_image_guid)

    if report_image.location:
        return

    if report_image.image_url:
        print report_image.image_url
        response = urllib2.urlopen(report_image.image_url)
        image = Image.open(StringIO.StringIO(response.read()))

        exif_data = get_exif_data(image)
        if (exif_data):
            lat, lon = get_lat_lon(exif_data)

            if lat and lon:
                report_image.location = 'POINT(%f %f)' % (lon, lat)
                report_image.save()


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


# !!!!!!!!!! Deprecate, don't add any your coding in this function !!!!!!!!!!!!
logger = get_task_logger(__name__)


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def send_data_to_spreadsheet_by_authority(report):
    authorities = Authority.objects.filter(
        administration_areas__id__in=get_administration_area_and_ancestors_ids(report.administration_area)).distinct()
    for authority in authorities:
        if authority.spreadsheet_key:
            template = report.type.django_template
            form_data = json.loads(report.form_data)
            t = Template(template)
            c = Context(form_data)
            template_rendered = t.render(c)
            template_rendered = re.sub(r'<(\/)*(\w)+>', '', template_rendered)

            data = {
                u'วันเดือนปี': report.date.strftime('%d/%m/%Y'),
                u'ประเภทรายงาน': report.type.name,
                u'เหตุแจ้ง': template_rendered,
                u'dashboard': 'http://www.cmonehealth.org/dashboard/#/reports/%s' % report.id,
                u'ผู้แจ้ง': report.created_by.get_full_name()
            }
            put_data_to_spreadsheet(authority.spreadsheet_key, data)


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def send_data_to_spreadsheet(report):
    spreadsheets = SpreadsheetResponse.objects.filter(report_types=report.type)
    spreadsheets = [spreadsheet for spreadsheet in spreadsheets if
                    has_permission_area_in_authorities(report.administration_area, spreadsheet.authorities)]

    for spreadsheet in spreadsheets:
        template = report.type.django_template
        form_data = json.loads(report.form_data)
        t = Template(template)
        c = Context(form_data)
        template_rendered = t.render(c)
        template_rendered = re.sub(r'<(\/)*(\w)+>', '', template_rendered)

        data = {
            u'วันเดือนปี': report.date.strftime('%d/%m/%Y'),
            u'ประเภทรายงาน': report.type.name,
            u'เหตุแจ้ง': template_rendered,
            u'dashboard': 'http://www.cmonehealth.org/dashboard/#/reports/%s' % report.id,
            u'ผู้แจ้ง': report.created_by.get_full_name()
        }
        put_data_to_spreadsheet(spreadsheet.key, data)


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def send_data_to_calendar(report):
    from django.utils import timezone
    now = timezone.now()

    calendars = GoogleCalendarResponse.objects.filter(report_states=report.state)
    calendars = [calendar for calendar in calendars if
                 has_permission_area_in_authorities(report.administration_area, calendar.authorities)]
    for calendar in calendars:
        template = calendar.render_template
        form_data = json.loads(report.form_data)
        t = Template(template)
        c = Context({'report': report, 'formData': form_data})
        template_rendered = t.render(c)
        template_rendered = re.sub(r'<(\/)*(\w)+>', '', template_rendered)
        data = {
            u'title': template_rendered,
            u'address': report.administration_area.address,
            u'description': '<a href="http://www.cmonehealth.org/dashboard/#/reports/%s">http://www.cmonehealth.org/dashboard/#/reports/%s</a>' % (
                report.id, report.id),
        }

        resp = put_event_to_calendar(calendar.calendar_id, data, now)
        if resp:
            event_id = resp['id']
            new_event, created = GoogleCalendarResponseEvent.objects.get_or_create(event_id=event_id,
                                                                                   data=json.dumps(data),
                                                                                   report=report,
                                                                                   calendar=calendar,
                                                                                   date=now)


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def delete_calendar_data(report):
    events = GoogleCalendarResponseEvent.objects.filter(report=report, deleted=False).order_by('id')

    for event in events:
        delete_calendar_events(event.calendar.calendar_id, event.event_id)

        event.deleted = True
        event.save()


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def undelete_calendar_data(report):
    events = GoogleCalendarResponseEvent.objects.filter(report=report, deleted=True).order_by('id')
    for event in events:
        calendar = event.calendar
        report = event.report
        data = json.loads(event.data)
        date = event.date
        resp = put_event_to_calendar(calendar.calendar_id, data, date)
        if resp:
            event_id = resp['id']
            new_event, created = GoogleCalendarResponseEvent.objects.get_or_create(event_id=event_id,
                                                                                   data=json.dumps(data),
                                                                                   report=report,
                                                                                   calendar=calendar,
                                                                                   date=date)
    events.delete()


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def report_cep(report_id, payload):
    from reports.models import Report
    if settings.ESPER_CONNECTION_URL:
        report = Report.objects.get(id=report_id)

        resp = requests.post('%sreport' % settings.ESPER_CONNECTION_URL, data=json.dumps(payload))
        print '======== CEP Response Code============='
        print resp.status_code
        print '==================================='
        from common.functions import get_system_user
        system_user = get_system_user()
        LogItem.objects.log_action(key='REPORT_TO_CEP',
                                   created_by=system_user,
                                   object1=report,
                                   object2=report.type,
                                   data={
                                       'data': payload['data'] if 'data' in payload else {},
                                       'name': payload['name'] if 'name' in payload else '',
                                       'status_code': resp.status_code
                                   })
        try:
            response = requests.post(
                url="https://www.google-analytics.com/collect",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                },
                data={
                    "v": "1",
                    "t": "event",
                    "ds": "podd-api",
                    "ec": "cep",
                    "ea": "report_cep",
                    "el": report_id,
                    "cd1": payload['name'] if 'name' in payload else '',
                    "cd2": resp.status_code,
                    "tid": "UA-164898471-1",
                    "cid": "99999",
                },
            )
            print('Google analytic Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
        except requests.exceptions.RequestException:
            print('Google analytic HTTP Request failed')
        except:
            print('Google error unknown')
        # Auto regenerate schema from report, state, case when Esper restart
        if resp.status_code == 500:
            if "Event type named '%s' could not be found" % report.get_schema_name() in resp.text:
                report.type.create_cep()
                for state in report.type.report_state_report_type.all():
                    state.create_cep()
                for case_definition in report.type.case_definition_report_type.all():
                    print 'create_cep', safe_str(case_definition)
                    case_definition.create_cep()

                report.create_cep()


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def report_sns_notification(report):
    if settings.SNS_REPORT_ENABLE:
        import boto3
        if report.negative:
            if report.type.code in settings.SNS_REPORT_MAPPING:
                arn = settings.SNS_REPORT_MAPPING[report.type.code]
                sns = boto3.client(
                    'sns',
                    aws_access_key_id=settings.SNS_ACCESS_KEY,
                    aws_secret_access_key=settings.SNS_SECRET_KEY,
                    region_name='ap-southeast-1'
                )
                reportData = ReportSerializer(report).data
                response = sns.publish(
                    TopicArn=arn,
                    Message=json.dumps(reportData)
                )
                print 'send sns', report.id, arn, response['MessageId']
