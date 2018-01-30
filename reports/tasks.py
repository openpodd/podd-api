# -*- encoding: utf-8 -*-

from __future__ import absolute_import

import json
import re
import StringIO
import urllib2
import requests
from celery.contrib.methods import task_method

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.gis.measure import D
from django.core.mail import send_mail
from django.template import Template, Context
from django.template.loader import render_to_string

from celery import shared_task
from PIL import Image

from accounts.models import (Configuration, User,  UserDevice, GroupReportType,
    GroupAdministrationArea, Authority)
from common.constants import (GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA,
    GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA, GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE,
    GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE, PRIORITY_IGNORE, PRIORITY_CONTACT, NEWS_TYPE_NEWS)
from common.decorators import domain_celery_task
from common.functions import (get_exif_data, get_lat_lon, get_administration_area_and_ancestors_ids,
    filter_permitted_administration_areas_and_descendants, publish_gcm_message, publish_sms_message,
    put_data_to_spreadsheet, publish_apns_message, has_permission_area_in_authorities, put_event_to_calendar,
    delete_calendar_events)
from flags.functions import create_flag_comment
from flags.serializers import FlagSerializer
from logs.models import LogItem
from notifications.functions import create_notification
from podd.celery import app, DomainTask
from reports.models import (ReportImage, SpreadsheetResponse, AdministrationArea, GoogleCalendarResponse,
                            GoogleCalendarResponseEvent)
from reports.pub_tasks import publish_report_flag
from celery.utils.log import get_task_logger


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
@app.task
def new_negative_report_rule(report):
    from common.functions import get_system_user
    user = get_system_user()

    if report.test_flag:
        ignore(report, user)

    if report.type.name == u'อื่นๆ' and not report.test_flag:
        '''
        IF REPORT TYPE == u'อื่น ๆ'
        - SET FLAG TO IGNORE
        '''
        ignore(report, user)

    elif report.type.name == u'สัตว์กัด' and not report.test_flag:
        '''
        IF REPORT TYPE == u'สัตว์กัด'
        - SET FLAG TO PROSPECT
        - SENT MAIL TO GROUP ALERT NEW REPORT -> CHECK AREA, REPORT TYPE
        '''

        comment = create_flag_comment(report=report, priority=PRIORITY_CONTACT, flag_owner=user)
        serializer = FlagSerializer(data={
            'reportId': report.id,
            'priority': PRIORITY_CONTACT,
        })
        if serializer.is_valid():
            serializer.object.comment = comment
            serializer.object.flag_owner = user
            serializer.save()

            publish_report_flag(serializer.data)

        # SEND MAIL
        send_alert_new_report_email(report)
        send_alert_new_report_sms(report)
        send_alert_new_report_gcm_message(report)

    elif report.type.name == u'สัตว์ป่วย/ตาย' and not report.test_flag:
        '''
        IF DEATHCOUNT > 2 OR SICKCOUNT > 10 OR NEARBYCOUNT > 2
        OR ห่าไก่ แอนแทรก ปากเท้าเปื่อย
        THEN
        - SET FLAG TO PROSPECT
        - SENT MAIL TO GROUP ALERT NEW REPORT -> CHECK AREA, REPORT TYPE
        '''

        form_data = json.loads(report.form_data)
        if form_data.get('disease') in [u'ห่าไก่', u'กาลี/แอนแทรกซ์', u'ปากและเท้าเปื่อย'] or \
            form_data.get('deathCount', 0) > 2 or form_data.get('sickCount', 0) > 10 or \
            form_data.get('nearByCount', 0) > 2:

            comment = create_flag_comment(report=report, priority=PRIORITY_CONTACT, flag_owner=user)
            serializer = FlagSerializer(data={
                'reportId': report.id,
                'priority': PRIORITY_CONTACT,
            })
            if serializer.is_valid():
                serializer.object.comment = comment
                serializer.object.flag_owner = user
                serializer.save()

                publish_report_flag(serializer.data)

            # SEND MAIL
            send_alert_new_report_email(report)
            send_alert_new_report_sms(report)
            send_alert_new_report_gcm_message(report)

    elif report.type.name in [u'อาหารปลอดภัย', u'สิ่งแวดล้อม', u'ภัยธรรมชาติ', u'เครื่องสำอาง/ยา', u'โรคสัตว์สู่คน'] and not report.test_flag:

         send_alert_new_report_email(report)
         send_alert_new_report_sms(report)

    # SEND EVERY NEGATIVE EMAIL TO SUPERUSER
    if not report.test_flag:
        send_alert_new_report_email_superuser(report)

        # send_data_to_spreadsheet_by_authority()
        send_data_to_spreadsheet(report)


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def send_data_to_spreadsheet_by_authority(report):
    authorities = Authority.objects.filter(administration_areas__id__in=get_administration_area_and_ancestors_ids(report.administration_area)).distinct()
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
    spreadsheets = [spreadsheet for spreadsheet in spreadsheets if has_permission_area_in_authorities(report.administration_area, spreadsheet.authorities)]

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
    calendars = [calendar for calendar in calendars if has_permission_area_in_authorities(report.administration_area, calendar.authorities)]
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
            u'description': '<a href="http://www.cmonehealth.org/dashboard/#/reports/%s">http://www.cmonehealth.org/dashboard/#/reports/%s</a>' % (report.id, report.id),
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
def send_alert_new_report_email_superuser(report):
    # FILTER PERMITTED GROUP ON REPORT TYPE
    allowed_report_type_groups = GroupReportType.objects.filter(report_type=report.type,
        group__type=GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE)

    allowed_report_type_emails = []
    for group in allowed_report_type_groups:
        allowed_report_type_emails.extend(group.group.user_set.filter(is_superuser=True).values_list('email', flat=True))

    # FILTER PERMITTED GROUP ON ADMINISTRATION AREA
    area_ids = get_administration_area_and_ancestors_ids(report.administration_area)
    allowed_administration_area_groups = GroupAdministrationArea.objects.filter(
        administration_area__in=area_ids, group__type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)

    allowed_administration_area_emails = []
    for group in allowed_administration_area_groups:
        allowed_administration_area_emails.extend(group.group.user_set.filter(is_superuser=True).values_list('email', flat=True))

    # INTERSECT BOTH PERMITTED GROUP ON REPORT TYPE AND AREA
    emails = list(set(allowed_report_type_emails) & set(allowed_administration_area_emails))
    emails = filter(None, emails)

    _send_new_report_email(report, emails)


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def send_alert_new_report_email(report):
    # FILTER PERMITTED GROUP ON REPORT TYPE
    allowed_report_type_groups = GroupReportType.objects.filter(report_type=report.type,
        group__type=GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE)

    allowed_report_type_emails = []
    for group in allowed_report_type_groups:
        allowed_report_type_emails.extend(group.group.user_set.filter(is_superuser=False).values_list('email', flat=True))

    # FILTER PERMITTED GROUP ON ADMINISTRATION AREA
    area_ids = get_administration_area_and_ancestors_ids(report.administration_area)
    allowed_administration_area_groups = GroupAdministrationArea.objects.filter(
        administration_area__in=area_ids, group__type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)

    allowed_administration_area_emails = []
    for group in allowed_administration_area_groups:
        allowed_administration_area_emails.extend(group.group.user_set.filter(is_superuser=False).values_list('email', flat=True))

    # INTERSECT BOTH PERMITTED GROUP ON REPORT TYPE AND AREA
    emails = list(set(allowed_report_type_emails) & set(allowed_administration_area_emails))
    emails = filter(None, emails)

    _send_new_report_email(report, emails)


def _send_new_report_email(report, emails):
    try:
        template = report.type.django_template
        form_data = json.loads(report.form_data)
        t = Template(template)
        c = Context(form_data)
        template_rendered = t.render(c)

        # EMAIL TITLE
        try:
            try:
                email_title_template = Configuration.objects.get(
                    system='web.email_template.alert_new_report', key='title:%s' % (report.type.code, ))
            except Configuration.DoesNotExist:
                email_title_template = Configuration.objects.get(
                    system='web.email_template.alert_new_report', key='title')
        except Configuration.DoesNotExist:
            email_title_template_rendered = u'{% if follow %}[ติดตาม] {% endif %}[PODD] รายงานผิดปกติของพื้นที่ %s ณ วันที่ %s [#%s]' % (
                report.administration_area.address,
                report.incident_date.strftime('%d-%m-%Y'),
                report.id
            )
        else:
            tt = Template(email_title_template.value)
            cc = Context({
                'report': report,
                'follow': report.parent != None
            })
            email_title_template_rendered = tt.render(cc)

        # EMAIL BODY
        try:
            try:
                email_body_template = Configuration.objects.get(
                    system='web.email_template.alert_new_report', key='body:%s' % (report.type.code, ))
            except Configuration.DoesNotExist:
                email_body_template = Configuration.objects.get(
                    system='web.email_template.alert_new_report', key='body')
        except Configuration.DoesNotExist:
            email_body_template_rendered = render_to_string(
                'email/alert_new_report.html', {
                    'template_rendered': template_rendered,
                    'report': report,
                }
            )
        else:
            tt = Template(email_body_template.value)
            cc = Context({
                'template_rendered': template_rendered,
                'report': report,
            })
            email_body_template_rendered = tt.render(cc)

        # SEND MAIL
        if settings.NOTIFICATION_DISABLED and settings.EMAIL_BACKEND != 'django.core.mail.backends.locmem.EmailBackend':
            print '------ EMAILS PARAMS ------'
            print '  ---- emails:', emails
            print '  ---- email_title_template_rendered:', email_title_template_rendered
            print '  ---- email_body_template_rendered:', email_body_template_rendered
            print '------ /EMAILS PARAMS -----'
        else:
            send_mail(
                email_title_template_rendered,
                email_body_template_rendered,
                settings.EMAIL_ADDRESS_NO_REPLY,
                emails,
            )

        # LOGGING
        from common.functions import get_system_user
        system = get_system_user()

        LogItem.objects.log_action(key='REPORT_SEND_MAIL_NEW_REPORT', created_by=system,
            object1=report, data={
                'emails': ','.join(emails)
            })
    except:
        import sys
        print sys.exc_info()


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def send_alert_new_report_gcm_message(report):
    try:
        device = UserDevice.objects.get(user=report.created_by)

        try:
            try:
                reply_message_to_reporter = Configuration.objects.get(
                    system='android.server.push_notification',
                    key='reply_message_to_reporter:%s' % (report.type.code, )
                ).value
            except Configuration.DoesNotExist:
                reply_message_to_reporter = Configuration.objects.get(system='android.server.push_notification',
                                                                      key='reply_message_to_reporter').value
        except Configuration.DoesNotExist:
            reply_message_to_reporter = u'<p>ขณะนี้ศูนย์ประสานงานโครงการผ่อดีดีได้รับรายงานเหตุผิดปกติของท่านแล้ว</p>' \
                + u'<p>เจ้าหน้าที่ศูนย์ประสานงานจะดำเนินการเก็บข้อมูล, ประเมินสถานการณ์ในเหตุผิดปกติ และอาจมีการติดต่อกลับไป</p>' \
                + u'<p>ขอความร่วมมือให้ท่านติดตามรายงานผิดปกติอย่างใกล้ชิด ขอบคุณค่ะ</p>'

        message_type = NEWS_TYPE_NEWS
        notification = create_notification(report=report, receive_user=report.created_by,
            message=reply_message_to_reporter, message_type=message_type)
        publish_gcm_message([device.gcm_reg_id], reply_message_to_reporter, message_type, notification.id)
        publish_apns_message([device.apns_reg_id], reply_message_to_reporter, notification.id)

    except UserDevice.DoesNotExist:
        pass


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def send_alert_new_report_sms(report):
    # FILTER PERMITTED GROUP ON REPORT TYPE
    allowed_report_type_groups = GroupReportType.objects.filter(report_type=report.type,
        group__type=GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE)

    allowed_report_type_telephones = []
    for group in allowed_report_type_groups:
        allowed_report_type_telephones.extend(group.group.user_set.values_list('telephone', flat=True))

    # FILTER PERMITTED GROUP ON ADMINISTRATION AREA
    area_ids = get_administration_area_and_ancestors_ids(report.administration_area)
    allowed_administration_area_groups = GroupAdministrationArea.objects.filter(
        administration_area__in=area_ids, group__type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)

    allowed_administration_area_telephones = []
    for group in allowed_administration_area_groups:
        allowed_administration_area_telephones.extend(group.group.user_set.values_list('telephone', flat=True))

    # INTERSECT BOTH PERMITTED GROUP ON REPORT TYPE AND AREA
    telephones = list(set(allowed_report_type_telephones) & set(allowed_administration_area_telephones))
    telephones = filter(None, telephones)
    try:
        try:
            new_report_sms = Configuration.objects.get(system='web.sms_templete.new_report',
                                                       key='message:%s' % (report.type.code, )).value
        except Configuration.DoesNotExist:
            new_report_sms = Configuration.objects.get(system='web.sms_templete.new_report', key='message').value
    except Configuration.DoesNotExist:
        new_report_sms = u'{% if follow %}[ติดตาม] {% endif %}มีรายงานประเภท {{ report.type.name }} {{ template_rendered }} ที่{{ report.administration_area.address }}' \
            + u' รายงานโดย {{ report.created_by.get_full_name }} ติดต่อกลับ {{ report.created_by.project_mobile_number }}' \
            + u'{% if report.created_by.telephone %}หรือ {{ report.created_by.telephone }}{% endif %}'

    template = report.type.django_template
    form_data = json.loads(report.form_data)
    t = Template(template)
    c = Context(form_data)
    template_rendered = t.render(c)
    template_rendered = re.sub(r'<(\/)*(\w)+>', '', template_rendered)

    tt = Template(new_report_sms)
    cc = Context({
        'report': report,
        'template_rendered': template_rendered,
        'follow': report.parent != None
    })

    new_report_sms_rendered = tt.render(cc)
    publish_sms_message(message=new_report_sms_rendered, telephones=telephones)


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def send_alert_new_case(flag):
    report = flag.comment.report

    # FILTER PERMITTED GROUP ON REPORT TYPE
    allowed_report_type_groups = GroupReportType.objects.filter(report_type=report.type,
        group__type=GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE)

    allowed_report_type_emails = []
    allowed_report_type_telephones = []
    for group in allowed_report_type_groups:
        allowed_report_type_emails.extend(group.group.user_set.values_list('email', flat=True))
        allowed_report_type_telephones.extend(group.group.user_set.values_list('telephone', flat=True))

    # FILTER PERMITTED GROUP ON ADMINISTRATION AREA
    area_ids = get_administration_area_and_ancestors_ids(report.administration_area)
    allowed_administration_area_groups = GroupAdministrationArea.objects.filter(
        administration_area__in=area_ids, group__type=GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA)

    allowed_administration_area_emails = []
    allowed_administration_area_telephones = []
    for group in allowed_administration_area_groups:
        allowed_administration_area_emails.extend(group.group.user_set.values_list('email', flat=True))
        allowed_administration_area_telephones.extend(group.group.user_set.values_list('telephone', flat=True))


    # INTERSECT BOTH PERMITTED GROUP ON REPORT TYPE AND AREA
    emails = list(set(allowed_report_type_emails) & set(allowed_administration_area_emails))
    emails = filter(None, emails)

    telephones = list(set(allowed_report_type_telephones) & set(allowed_administration_area_telephones))
    telephones = filter(None, telephones)

    try:
        template = report.type.django_template
        form_data = json.loads(report.form_data)
        t = Template(template)
        c = Context(form_data)
        template_rendered = t.render(c)

        # EMAIL TITLE
        try:
            email_title_template = Configuration.objects.get(
                system='web.email_template.alert_new_case', key='title')
        except Configuration.DoesNotExist:
            email_title_template_rendered = u'[PODD] เคสรายงานผิดปกติของพื้นที่ %s ณ วันที่ %s [#%s]' % (
                report.administration_area.address,
                report.incident_date.strftime('%d-%m-%Y'),
                report.id
            )
        else:
            tt = Template(email_title_template.value)
            cc = Context({
                'report': report,
            })
            email_title_template_rendered = tt.render(cc)

        # EMAIL BODY
        try:
            email_body_template = Configuration.objects.get(
                system='web.email_template.alert_new_case', key='body')
        except Configuration.DoesNotExist:
            email_body_template_rendered = render_to_string(
                'email/alert_new_case.html', {
                    'template_rendered': template_rendered,
                    'report': report,
                    'flag': flag,
                }
            )
        else:
            tt = Template(email_body_template.value)
            cc = Context({
                'template_rendered': template_rendered,
                'report': report,
            })
            email_body_template_rendered = tt.render(cc)

        # SEND MAIL
        send_mail(
            email_title_template_rendered,
            email_body_template_rendered,
            settings.EMAIL_ADDRESS_NO_REPLY,
            emails,
        )

        # LOGGING
        from common.functions import get_system_user
        system = get_system_user()

        LogItem.objects.log_action(key='REPORT_SEND_MAIL_NEW_CASE', created_by=system,
            object1=report, data={
                'emails': ','.join(emails)
            })

        # FOR NOTIFICATION BY GCM
        allowed_report_type_ids = []
        for group in allowed_report_type_groups:
            allowed_report_type_ids.extend(group.group.user_set.values_list('id', flat=True))

        allowed_administration_area_ids = []
        for group in allowed_administration_area_groups:
            allowed_administration_area_ids.extend(group.group.user_set.values_list('id', flat=True))

        # INTERSECT BOTH PERMITTED GROUP ON REPORT TYPE AND AREA
        ids = list(set(allowed_report_type_ids) & set(allowed_administration_area_ids))
        ids = filter(None, ids)

        devices = UserDevice.objects.filter(user__id__in=ids)
        gcm_devices = list(devices.values_list('gcm_reg_id', flat=True))
        apns_devices = list(devices.values_list('apns_reg_id', flat=True))

        # ALERT NEW CASE MESSEGE
        try:
            new_case_message = Configuration.objects.get(system='android.server.push_notification', key='new_case_message')
        except Configuration.DoesNotExist:
            pass
        else:
            if report.created_by.project_mobile_number:
                project_mobile_number_link = report.created_by.project_mobile_number.split('0',1)[1]
            else:
                project_mobile_number_link = ''

            message_type = 'news'
            tt = Template(new_case_message.value)
            cc = Context({
                'template_rendered': template_rendered,
                'report': report,
                'project_mobile_number_link': project_mobile_number_link,
                'flag': flag
            })
            new_case_message_rendered = tt.render(cc)

            for device in devices:
                notification = create_notification(report=report, receive_user=device.user, message=new_case_message_rendered, message_type=message_type)

            publish_gcm_message(gcm_devices, new_case_message_rendered, message_type)
            publish_apns_message(apns_devices, new_case_message_rendered)

        # ALERT NEW CASE SMS
        try:
            new_case_sms = Configuration.objects.get(system='web.sms_templete.new_case', key='message').value
        except Configuration.DoesNotExist:
            new_case_sms = u'เกิดเหตุประเภท {{ report.type.name }} {{ template_rendered }} ที่{{ report.administration_area.address }}' \
            + u' รายงานโดย {{ report.created_by.get_full_name  }} ติดต่อกลับ {{ report.created_by.project_mobile_number }}' \
            + u'{% if report.created_by.telephone %}หรือ {{ report.created_by.telephone }}{% endif %}'
        else:
            template = report.type.django_template
            form_data = json.loads(report.form_data)
            t = Template(template)
            c = Context(form_data)
            template_rendered = t.render(c)
            template_rendered = re.sub(r'<(\/)*(\w)+>', '', template_rendered)

            tt = Template(new_case_sms)
            cc = Context({
                'report': report,
                'template_rendered': template_rendered,
            })
            new_case_sms_rendered = tt.render(cc)
            publish_sms_message(message=new_case_sms_rendered, telephones=telephones)

    except:
        import sys
        print sys.exc_info()


@app.task(base=DomainTask, bind=True)
@domain_celery_task
def report_cep(report_id, payload):

    from reports.models import Report

    if settings.ESPER_CONNECTION_URL:
        resp = requests.post('%sreport' % settings.ESPER_CONNECTION_URL, data=json.dumps(payload))
        print '======== CEP Response Code============='
        print resp.status_code
        print '==================================='
        report = Report.objects.get(id=report_id)

        # Auto regenerate schema from report, state, case when Esper restart
        if resp.status_code == 500:
            if "Event type named '%s' could not be found" % report.get_schema_name() in resp.text:
                report.type.create_cep()
                for state in report.type.report_state_report_type.all():
                    state.create_cep()
                for case_definition in report.type.case_definition_report_type.all():

                    print 'create_cep', case_definition
                    case_definition.create_cep()

                report.create_cep()


