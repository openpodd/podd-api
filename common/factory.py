# -*- encoding: utf-8 -*-

import datetime
import json
from random import randint
from uuid import uuid1

from django.contrib.auth.models import Group
from django.utils.text import slugify

from rest_framework.authtoken.models import Token

from accounts.models import (User, GroupReportType, GroupAdministrationArea, Configuration,
    UserDevice, CustomPermission, Authority, UserCode, GroupInvite)
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA, GROUP_WORKING_TYPE_REPORT_TYPE, NEWS_TYPE_NEWS
from flags.models import Flag
from reports.models import Report, ReportType, AdministrationArea, ReportComment, ReportImage
from mentions.models import Mention
from notifications.models import Notification


def randstr():
    return str(uuid1())[0: 10].replace('-', '')


def randnum(min=0, max=1000000):
    return randint(min, max)


def create_user(username=None, last_name=None, email=None, project_mobile_number=None, password='password', is_superuser=False,
    is_staff=False, with_token=True, administration_area=None, display_password='password', status='' , serial_number=None, telephone='',
    is_anonymous=False, is_public=False):

    username = username or randstr()
    last_name = last_name or randstr()
    email = email or '%s@kmail.com' % username
    project_mobile_number = project_mobile_number or '0811111111'
    serial_number = serial_number or '0000000000000'

    user = User.objects.create_user(
        username = username,
        first_name = username,
        last_name = last_name,
        email = email,
        password = password,
        project_mobile_number = project_mobile_number,
        administration_area = administration_area,
        display_password = display_password,
        status = status,
        serial_number = serial_number,
        telephone = telephone,
        is_anonymous = is_anonymous,
        is_public = is_public,
    )
    user.is_superuser = is_superuser
    user.is_staff = is_staff
    user.save()

    if with_token:
        Token.objects.create(user=user)

    return user

def create_user_device(user=None, android_id=None, device_id=None, brand='Samsung',
    model='Galaxy-S', wifi_mac='Dcd2-12D3-W43s', gcm_reg_id=None):

    user = user or create_user()
    android_id = android_id or 'A-%s' % randstr()
    device_id = device_id or 'D-%s' % randstr()
    gcm_reg_id = gcm_reg_id or 'GCM-%s' % randstr()

    device = UserDevice.objects.create(
        user = user,
        android_id = android_id,
        device_id = device_id,
        brand = brand,
        model = model,
        wifi_mac = wifi_mac,
        gcm_reg_id = gcm_reg_id,
    )
    return device

def create_group(name=None, type=0):
    name = name or 'G-%s' % randstr()

    group = Group.objects.create(
        name = name,
        type = type,
    )
    return group

def create_invite_group(name=None):
    name = name or 'G-%s' % randstr()

    group_invite = GroupInvite.objects.create(
        name = name,
    )
    return group_invite

def create_group_type_report_type(name=None):
    group = create_group(name, type=GROUP_WORKING_TYPE_REPORT_TYPE)
    return group

def create_group_type_administration_area(name=None):
    group = create_group(name, type=GROUP_WORKING_TYPE_ADMINSTRATION_AREA)
    return group

def add_user_to_new_group(user, type=0):
    group = create_group(type=type)
    user.groups.add(group)
    return group

def add_user_to_new_group_type_report_type(user):
    group = create_group_type_report_type()
    user.groups.add(group)
    return group

def add_user_to_new_group_type_administration_area(user):
    group = create_group_type_administration_area()
    user.groups.add(group)
    return group

def create_custom_permission(name=None, codename=None):
    name = name or 'P %s' % randstr()
    codename = codename or slugify(unicode(name))

    perm = CustomPermission.objects.create(
        name = name,
        codename = codename,
    )
    return perm

def create_report_type(name=None, code=None, form_definition={}, version=1,
    template='There are {{ sickCount }} sick animals', authority=None):

    name = name or 'RT-%s' % randstr()
    code = code or randstr()
    form_definition = form_definition or {
        "startPageId": 1,
        "questions": [
            {
                "id": 1,
                "name": "animal_group",
                "title": u"ประเภทสัตว์",
                "type": "single",
                "items": [
                    { "id": u"สัตว์ปีก", "text": u"สัตว์ปีก" },
                    { "id": u"สัตว์กระเพาะเดี่ยว", "text": u"สัตว์กระเพาะเดี่ยว" },
                    { "id": u"สัตว์กระเพาะรวม", "text": u"สัตว์กระเพาะรวม" }
                ],
                "validations": [
                    { "type": "require", "message": u"กรุณาระบุประเภทสัตว์" }
                ]
            },
        ]
    }

    type = ReportType.objects.create(
        name = name,
        code = code,
        form_definition = json.dumps(form_definition),
        version = version,
        template = template,
        authority = authority
    )

    return type


def create_administration_area(name=None, location='POINT (100.552206 13.808277)', address=None, authority=None, contacts='', mpoly=None):
    name = name or 'AA-%s' % randstr()
    address = address or '%s, Seoul, South Korea' % name
    authority_name = randstr()
    authority = authority or Authority.objects.create(code=authority_name, name=authority_name)

    area = AdministrationArea.objects.create(
        name = name,
        location = location,
        address = address,
        authority = authority,
        contacts = contacts,
        mpoly=mpoly
    )
    return area


def add_child_administration_area(area, name=None, location='POINT (100.552206 13.808277)', address=None):
    name = name or 'AAs-%s' % randstr()
    address = address or '%s, Seoul, South Korea' % name

    subarea = area.add_child(
        name = name,
        location = location,
        address = address,
    )
    return subarea


def create_group_report_type(group=None, report_type=None):
    group = group or create_group()
    report_type = report_type or create_report_type()

    group_report_type = GroupReportType.objects.create(
        group = group,
        report_type = report_type,
    )
    return group_report_type

def create_group_administration_area(group=None, administration_area=None):
    group = group or create_group()
    administration_area = administration_area or create_administration_area()

    group_administration_area = GroupAdministrationArea.objects.create(
        group = group,
        administration_area = administration_area,
    )
    return group_administration_area

def create_report(report_id=None, guid=None, report_location='POINT (99.000720 18.785830)',
    administration_location='POINT (100.552206 13.808277)', administration_area=None,
    type=None, date=datetime.datetime.now(), incident_date=datetime.date.today(), form_data={},
    negative=True, created_by=None, parent=None, test_flag=None, add_default_administration_area=True, add_default_report_location=True):

    report_id = report_id or randnum()
    guid = guid or randstr()
    type = type or create_report_type()
    form_data = form_data or {
        "symptom": "cough,fever,pain",
        "sickCount": 4,
    }
    created_by = created_by or create_user()

    data = {
        'report_id': report_id,
        'guid': guid,
        'administration_location': administration_location,
        'type': type,
        'parent': parent,
        'date': date,
        'incident_date': incident_date,
        'form_data': json.dumps(form_data),
        'negative': negative,
        'created_by': created_by,
        'test_flag': test_flag
    }

    if add_default_administration_area:
        administration_area = administration_area or create_administration_area()
        data['administration_area'] = administration_area

    if add_default_report_location:
        data['report_location'] = report_location


    report = Report.objects.create(**data)

    return report

def create_report_image(report=None, guid=None, note='This is iPhone6+',
    image_url='http://i.imgur.com/yRiCYEc.jpg',
    thumbnail_url='http://taeyeonism.com/wp-content/uploads/2014/09/mnet-wide-33.jpg'):

    report = report or create_report()
    guid = guid or randstr()

    image = ReportImage.objects.create(
        report = report,
        guid = guid,
        note = note,
        image_url = image_url,
        thumbnail_url = thumbnail_url,
    )
    return image


def create_report_comment(report=None, message='Hello Comment', created_by=None):
    report = report or create_report()
    created_by = created_by or create_user()

    report_comment = ReportComment.objects.create(
        report = report,
        message = message,
        created_by = created_by,
    )
    return report_comment

def create_configuration(system='android.configuration', key=None, value=None):
    key = key or 'K-%s' % randstr()
    value = value or 'V-%s' % randstr()

    configuration = Configuration.objects.create(
        system = system,
        key = key,
        value = value,
    )
    return configuration

def create_mention(comment=None, mentioner=None, mentionee=None, is_notified=False, seen_at=None):
    comment = comment or create_report_comment()
    mentioner = mentioner or create_user()
    mentionee = mentionee or create_user()

    mention = Mention.objects.create(
        comment = comment,
        mentioner = mentioner,
        mentionee = mentionee,
        is_notified = is_notified,
        seen_at = seen_at,
    )
    return mention

def create_flag(priority=0, report=None, flag_owner=None):
    report = report or create_report()
    comment =  create_report_comment(report=report)
    flag_owner = flag_owner or create_user()
    
    flag = Flag.objects.create(
        priority = priority,
        comment = comment,
        flag_owner = flag_owner,
    )
    return flag

def create_notification(report=None, receive_user=None, message='welcome', message_type='news'):
    report = report or create_report()
    receive_user = receive_user or create_user()

    notification = Notification.objects.create(
        report = report,
        receive_user = receive_user,
        message = message,
        type = NEWS_TYPE_NEWS,
        to = receive_user,
    )
    return notification
    
def create_authority(code=None, name=None):
    code = code or randstr()
    name = name or code
    authority = Authority.objects.create(
        code = code,
        name = name,
    )
    return authority

def create_user_code(user=None):
    user = user or create_user()

    user_code = UserCode(user=user)
    user_code.save()
    return user_code


