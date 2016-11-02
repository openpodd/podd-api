# -*- encoding: utf-8 -*-

import datetime
import json
import urllib2
from django.conf import settings

from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test.client import encode_multipart
from django.utils import timezone
from mock import patch
from mock import mock_open
from mockredis import mock_strict_redis_client
from rest_framework.test import APITestCase

from common import factory
from common.constants import (PRIORITY_FOLLOW, GROUP_WORKING_TYPE_REPORT_TYPE,
    GROUP_WORKING_TYPE_ADMINSTRATION_AREA, GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA,
    GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE, USER_STATUS_ADDITION_VOLUNTEER, SUPPORT_LIKE_ME_TOO_COMMENT,
    SUPPORT_COMMENT, SUPPORT_LIKE_ME_TOO, SUPPORT_LIKE, SUPPORT_ME_TOO)
from flags.models import Flag
from mentions.models import Mention
from notifications.models import Notification
from reports.models import Report, ReportImage, ReportComment, ReportType, ReportAbuse
from reports.tests.test_models import common_public_setup
from summary.tests.test_api import order_list_by_id


def mock_upload_to_s3(file):
    return file.name


def get_temporary_file():
    m = mock_open()
    with patch('__main__.open', m, create=True):
        temporary_file = open('/tmp/hello.world.jpg', 'w')
        file = File(temporary_file)
        file.write(urllib2.urlopen('http://www.yespetshop.com/private_folder/kitten-1.jpg').read())
        file.closed
        temporary_file.closed
    return temporary_file

get_temporary_file()


def get_large_temporary_file():
    m = mock_open()
    with patch('__main__.open', m, create=True):
        temporary_file = open('/tmp/hello_large.world', 'w')
        file = File(temporary_file)
        file.write(urllib2.urlopen('http://www.nasa.gov/pdf/703154main_earth_art-ebook.pdf').read())
        file.closed
        temporary_file.closed
    return temporary_file


@patch('django_redis.get_redis_connection', mock_strict_redis_client)
class TestApiReportList(APITestCase):
    def setUp(self):

        try:
            self.default_positive_type = ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            self.default_positive_type = ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.yoona)

        self.authority_1 = factory.create_authority()
        self.authority.users.add(self.taeyeon)

        self.authority_2 = factory.create_authority()
        self.authority.users.add(self.jessica)

        self.type1 = factory.create_report_type(authority=self.authority)
        self.type2 = factory.create_report_type(authority=self.authority)
        self.type3 = factory.create_report_type(authority=self.authority_2)

        self.area1 = factory.create_administration_area(authority=self.authority_1)
        self.area2 = factory.create_administration_area(authority=self.authority_1)
        self.area3 = factory.create_administration_area(authority=self.authority_2)

        self.authority_1.inherits.add(self.authority)

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type2,
            administration_area=self.area2, form_data={
                "symptom": u"cough,ปวดหัว,stiff",
                "sickCount": 5,
        }, date=datetime.datetime(2014, 11, 7, 12, 30, 45))
        self.report2 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area1, date=datetime.datetime(2014, 11, 11, 12, 30, 45))
        self.report3 = factory.create_report(created_by=self.jessica, type=self.type1,
            administration_area=self.area2, date=datetime.datetime(2014, 11, 9, 13, 30, 45))
        self.report4 = factory.create_report(type=self.type3, administration_area=self.area2)
        self.report5 = factory.create_report(type=self.type1, administration_area=self.area3)

        self.flag = factory.create_flag(report=self.report1, priority=1, flag_owner=self.taeyeon)

    def test_api_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)
        self.assertEqual(report1['reportId'], self.report2.report_id)
        self.assertEqual(report1['guid'], self.report2.guid)
        self.assertEqual(report1['reportTypeId'], self.report2.type.id)
        self.assertEqual(report1['administrationAreaId'], self.report2.administration_area.id)
        self.assertEqual(report1['negative'], self.report2.negative)
        self.assertEqual(report1['createdByName'], self.report2.created_by.get_full_name())
        self.assertEqual(report1['date'], self.report2.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report1['incidentDate'], self.report2.incident_date.strftime('%Y-%m-%d'))

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)
        self.assertEqual(report2['reportId'], self.report3.report_id)
        self.assertEqual(report2['guid'], self.report3.guid)
        self.assertEqual(report2['reportTypeId'], self.report3.type.id)
        self.assertEqual(report2['administrationAreaId'], self.report3.administration_area.id)
        self.assertEqual(report2['negative'], self.report3.negative)
        self.assertEqual(report2['createdByName'], self.report3.created_by.get_full_name())
        self.assertEqual(report2['date'], self.report3.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report2['incidentDate'], self.report3.incident_date.strftime('%Y-%m-%d'))

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)
        self.assertEqual(report3['reportId'], self.report1.report_id)
        self.assertEqual(report3['guid'], self.report1.guid)
        self.assertEqual(report3['reportTypeId'], self.report1.type.id)
        self.assertEqual(report3['administrationAreaId'], self.report1.administration_area.id)
        self.assertEqual(report3['negative'], self.report1.negative)
        self.assertEqual(report3['createdByName'], self.report1.created_by.get_full_name())
        self.assertEqual(report3['date'], self.report1.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report3['incidentDate'], self.report1.incident_date.strftime('%Y-%m-%d'))

    def test_api_report_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)
        self.assertEqual(report1['reportId'], self.report2.report_id)
        self.assertEqual(report1['guid'], self.report2.guid)
        self.assertEqual(report1['reportTypeId'], self.report2.type.id)
        self.assertEqual(report1['administrationAreaId'], self.report2.administration_area.id)
        self.assertEqual(report1['negative'], self.report2.negative)
        self.assertEqual(report1['createdByName'], self.report2.created_by.get_full_name())
        self.assertEqual(report1['date'], self.report2.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report1['incidentDate'], self.report2.incident_date.strftime('%Y-%m-%d'))
        # self.assertEqual(report1['flag'], '')

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)
        self.assertEqual(report2['reportId'], self.report3.report_id)
        self.assertEqual(report2['guid'], self.report3.guid)
        self.assertEqual(report2['reportTypeId'], self.report3.type.id)
        self.assertEqual(report2['administrationAreaId'], self.report3.administration_area.id)
        self.assertEqual(report2['negative'], self.report3.negative)
        self.assertEqual(report2['createdByName'], self.report3.created_by.get_full_name())
        self.assertEqual(report2['date'], self.report3.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report2['incidentDate'], self.report3.incident_date.strftime('%Y-%m-%d'))
        # self.assertEqual(report2['flag'], '')

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)
        self.assertEqual(report3['reportId'], self.report1.report_id)
        self.assertEqual(report3['guid'], self.report1.guid)
        self.assertEqual(report3['reportTypeId'], self.report1.type.id)
        self.assertEqual(report3['administrationAreaId'], self.report1.administration_area.id)
        self.assertEqual(report3['negative'], self.report1.negative)
        self.assertEqual(report3['createdByName'], self.report1.created_by.get_full_name())
        self.assertEqual(report3['date'], self.report1.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report3['incidentDate'], self.report1.incident_date.strftime('%Y-%m-%d'))
        # self.assertEqual(report3['flag'], '1')

    def test_api_report_with_pagination(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'page_size': 2
        }
        response = self.client.get(reverse('report-list'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)
        self.assertEqual(len(response_json['results']), 2)

        params = {
            'page_size': 2,
            'page': 2
        }
        response = self.client.get(reverse('report-list'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)
        self.assertEqual(len(response_json['results']), 1)

    def test_api_report_with_pagination_wih_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            'page_size': 2
        }
        response = self.client.get(reverse('report-list'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)
        self.assertEqual(len(response_json['results']), 2)

        params = {
            'page_size': 2,
            'page': 2
        }
        response = self.client.get(reverse('report-list'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)
        self.assertEqual(len(response_json['results']), 1)

    def test_api_return_report_only_administration_area_in_group_role_reporter(self):
        group_a = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)
        area = factory.create_administration_area()
        factory.create_group_administration_area(group=group_a, administration_area=area)

        report = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

    def test_api_return_report_only_report_type_in_group_role_reporter(self):
        group_r = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE)
        newtype = factory.create_report_type()
        factory.create_group_report_type(group=group_r, report_type=newtype)

        report = factory.create_report(created_by=self.taeyeon, type=newtype,
            administration_area=self.area2)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

    def test_api_report_with_form_data(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'withFormData': True
        }
        response = self.client.get(reverse('report-list'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)
        self.assertEqual(report1['formData'], json.loads(self.report2.form_data))

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)
        self.assertEqual(report2['formData'], json.loads(self.report3.form_data))

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)
        self.assertEqual(report3['formData'], json.loads(self.report1.form_data))

    def test_api_report_with_form_data_and_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            'withFormData': True
        }
        response = self.client.get(reverse('report-list'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)
        self.assertEqual(report1['formData'], json.loads(self.report2.form_data))

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)
        self.assertEqual(report2['formData'], json.loads(self.report3.form_data))

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)
        self.assertEqual(report3['formData'], json.loads(self.report1.form_data))

    '''
    def test_api_report_list_will_return_report_that_area_is_child_of_permitted_administration_area(self):
        area = self.area1.add_child(name='Namsan', location=self.area1.location)
        report = factory.create_report(type=self.type1, administration_area=area,
            date=datetime.datetime(2014, 10, 9, 13, 30, 45))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 4)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

        report4 = response_json['results'][3]
        self.assertEqual(report4['id'], report.id)

    def test_api_report_list_will_return_report_that_area_is_child_of_permitted_administration_area_with_authority(self):
        area = self.area1.add_child(name='Namsan', location=self.area1.location)
        report = factory.create_report(type=self.type1, administration_area=area,
            date=datetime.datetime(2014, 10, 9, 13, 30, 45))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 4)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

        report4 = response_json['results'][3]
        self.assertEqual(report4['id'], report.id)
    '''

    def test_api_report_filter_by_user(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'createdBy': self.taeyeon.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report1.id)

    def test_api_report_filter_by_user_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'createdBy': self.taeyeon.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report1.id)

    def test_api_report_filter_by_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'type': self.type2.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

    def test_api_report_filter_by_report_type_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'type': self.type2.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

    def test_api_report_filter_by_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'administrationArea': self.area1.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

    def test_api_report_filter_by_administration_area_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'administrationArea': self.area1.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

    def test_api_report_filter_by_form_data(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'symptom': u'ปวดหัว'
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

        response = self.client.get(reverse('report-list'), {
            'symptom': 'fever'
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_filter_by_form_data_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'symptom': u'ปวดหัว'
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

        response = self.client.get(reverse('report-list'), {
            'symptom': 'fever'
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_filter_multiple_value_in_one_field(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'symptom__in': [u'ปวดหัว', 'fever'],
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

    def test_api_report_filter_multiple_value_in_one_field_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'symptom__in': [u'ปวดหัว', 'fever'],
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

    def test_api_report_filter_multiple_value_in_one_field_part_2(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list') + u'?symptom__in=stiff&symptom__in=fever')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

    def test_api_report_filter_multiple_value_in_one_field_part_2_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list') + u'?symptom__in=stiff&symptom__in=fever')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

    def test_api_report_filter_greater_than_value(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'sickCount__gt': 4,
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

    def test_api_report_filter_greater_than_value_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'sickCount__gt': 4,
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

    def test_api_report_filter_multiple_data(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'symptom': 'fever',
            'createdBy': self.taeyeon.id,
            'type': self.type1.id,
            'administrationArea': self.area1.id,
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

    def test_api_report_filter_multiple_data_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'symptom': 'fever',
            'createdBy': self.taeyeon.id,
            'type': self.type1.id,
            'administrationArea': self.area1.id,
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

    def test_api_report_filter_results_only_have_permission_on_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'type': self.type3.id,
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 0)

    def test_api_report_filter_results_only_have_permission_on_report_type_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'type': self.type3.id,
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 0)

    def test_api_report_filter_results_only_have_permission_on_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'administrationArea': self.area3.id,
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 0)

    def test_api_report_filter_results_only_have_permission_on_administration_area_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'), {
            'administrationArea': self.area3.id,
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 0)
    '''
    def test_api_report_list_will_always_return_report_type_0(self):
        factory.create_report(type=self.default_positive_type, administration_area=self.area1, negative=False)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 4)

    def test_api_report_list_will_always_return_report_type_0_with_authority(self):
        factory.create_report(type=self.default_positive_type, administration_area=self.area1, negative=False)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 4)
    '''

    def test_anonymous_cannot_access_api_list_reports(self):
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 401)


@patch('django_redis.get_redis_connection', mock_strict_redis_client)
class TestApiReportSearch(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.taeyeon.last_name = 'Kim'
        self.taeyeon.save()
        self.jessica = factory.create_user()
        self.jessica.last_name = 'Jung'
        self.jessica.save()
        self.yoona = factory.create_user()
        self.yoona.last_name = 'Im'
        self.yoona.save()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.yoona)

        self.authority_1 = factory.create_authority()
        self.authority_1.users.add(self.jessica)

        self.type1 = factory.create_report_type(authority=self.authority)
        self.type2 = factory.create_report_type(authority=self.authority)
        self.type3 = factory.create_report_type(authority=self.authority_1)

        self.area1 = factory.create_administration_area(authority=self.authority)
        self.area2 = factory.create_administration_area(authority=self.authority)
        self.area3 = factory.create_administration_area(authority=self.authority_1)

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type2,
            administration_area=self.area2, form_data={
                "symptom": u"cough,ปวดหัว,stiff",
                "sickCount": 5,
        }, date=datetime.datetime(2014, 11, 7, 12, 30, 45))
        self.report2 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area1, date=datetime.datetime(2014, 11, 11, 12, 30, 45))
        self.report3 = factory.create_report(created_by=self.jessica, type=self.type1,
            administration_area=self.area2, date=datetime.datetime(2014, 11, 9, 13, 30, 45))
        self.report4 = factory.create_report(type=self.type3, administration_area=self.area2)
        self.report5 = factory.create_report(type=self.type1, administration_area=self.area3)

    def test_api_report_search(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)
        self.assertEqual(report1['reportId'], self.report2.report_id)
        self.assertEqual(report1['guid'], self.report2.guid)
        self.assertEqual(report1['reportTypeId'], self.report2.type.id)
        self.assertEqual(report1['administrationAreaId'], self.report2.administration_area.id)
        self.assertEqual(report1['negative'], self.report2.negative)
        self.assertEqual(report1['createdByName'], self.report2.created_by.get_full_name())
        self.assertEqual(report1['date'], self.report2.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report1['incidentDate'], self.report2.incident_date.strftime('%Y-%m-%d'))

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)
        self.assertEqual(report2['reportId'], self.report3.report_id)
        self.assertEqual(report2['guid'], self.report3.guid)
        self.assertEqual(report2['reportTypeId'], self.report3.type.id)
        self.assertEqual(report2['administrationAreaId'], self.report3.administration_area.id)
        self.assertEqual(report2['negative'], self.report3.negative)
        self.assertEqual(report2['createdByName'], self.report3.created_by.get_full_name())
        self.assertEqual(report2['date'], self.report3.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report2['incidentDate'], self.report3.incident_date.strftime('%Y-%m-%d'))

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)
        self.assertEqual(report3['reportId'], self.report1.report_id)
        self.assertEqual(report3['guid'], self.report1.guid)
        self.assertEqual(report3['reportTypeId'], self.report1.type.id)
        self.assertEqual(report3['administrationAreaId'], self.report1.administration_area.id)
        self.assertEqual(report3['negative'], self.report1.negative)
        self.assertEqual(report3['createdByName'], self.report1.created_by.get_full_name())
        self.assertEqual(report3['date'], self.report1.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report3['incidentDate'], self.report1.incident_date.strftime('%Y-%m-%d'))

    def test_api_report_search_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)
        self.assertEqual(report1['reportId'], self.report2.report_id)
        self.assertEqual(report1['guid'], self.report2.guid)
        self.assertEqual(report1['reportTypeId'], self.report2.type.id)
        self.assertEqual(report1['administrationAreaId'], self.report2.administration_area.id)
        self.assertEqual(report1['negative'], self.report2.negative)
        self.assertEqual(report1['createdByName'], self.report2.created_by.get_full_name())
        self.assertEqual(report1['date'], self.report2.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report1['incidentDate'], self.report2.incident_date.strftime('%Y-%m-%d'))

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)
        self.assertEqual(report2['reportId'], self.report3.report_id)
        self.assertEqual(report2['guid'], self.report3.guid)
        self.assertEqual(report2['reportTypeId'], self.report3.type.id)
        self.assertEqual(report2['administrationAreaId'], self.report3.administration_area.id)
        self.assertEqual(report2['negative'], self.report3.negative)
        self.assertEqual(report2['createdByName'], self.report3.created_by.get_full_name())
        self.assertEqual(report2['date'], self.report3.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report2['incidentDate'], self.report3.incident_date.strftime('%Y-%m-%d'))

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)
        self.assertEqual(report3['reportId'], self.report1.report_id)
        self.assertEqual(report3['guid'], self.report1.guid)
        self.assertEqual(report3['reportTypeId'], self.report1.type.id)
        self.assertEqual(report3['administrationAreaId'], self.report1.administration_area.id)
        self.assertEqual(report3['negative'], self.report1.negative)
        self.assertEqual(report3['createdByName'], self.report1.created_by.get_full_name())
        self.assertEqual(report3['date'], self.report1.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report3['incidentDate'], self.report1.incident_date.strftime('%Y-%m-%d'))

    def test_api_report_search_with_pagination(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'page_size': 2
        }
        response = self.client.get(reverse('reports_search'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)
        self.assertEqual(len(response_json['results']), 2)

        params = {
            'page_size': 2,
            'page': 2
        }
        response = self.client.get(reverse('reports_search'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)
        self.assertEqual(len(response_json['results']), 1)

    def test_api_report_search_with_pagination_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            'page_size': 2
        }
        response = self.client.get(reverse('reports_search'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)
        self.assertEqual(len(response_json['results']), 2)

        params = {
            'page_size': 2,
            'page': 2
        }
        response = self.client.get(reverse('reports_search'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)
        self.assertEqual(len(response_json['results']), 1)

    def test_api_report_search_filter_date_lt(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'date__lt': '2014-11-11T12:30:45Z'
        }
        response = self.client.get(reverse('reports_search'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)
        self.assertEqual(len(response_json['results']), 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report3.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report1.id)

    def test_api_report_search_filter_date_lt_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            'date__lt': '2014-11-11T12:30:45Z'
        }
        response = self.client.get(reverse('reports_search'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)
        self.assertEqual(len(response_json['results']), 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report3.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report1.id)

    def test_api_report_search_return_report_only_administration_area_in_group_role_reporter(self):
        group_a = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)
        area = factory.create_administration_area()
        factory.create_group_administration_area(group=group_a, administration_area=area)

        report = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

    def test_api_report_search_return_report_only_report_type_in_group_role_reporter(self):
        group_r = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE)
        newtype = factory.create_report_type()
        factory.create_group_report_type(group=group_r, report_type=newtype)

        report = factory.create_report(created_by=self.taeyeon, type=newtype,
            administration_area=self.area2)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

    def test_api_report_search_with_form_data(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'withFormData': True
        }
        response = self.client.get(reverse('reports_search'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)
        self.assertEqual(report1['formData'], json.loads(self.report2.form_data))

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)
        self.assertEqual(report2['formData'], json.loads(self.report3.form_data))

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)
        self.assertEqual(report3['formData'], json.loads(self.report1.form_data))

    def test_api_report_search_with_form_data_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            'withFormData': True
        }
        response = self.client.get(reverse('reports_search'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)
        self.assertEqual(report1['formData'], json.loads(self.report2.form_data))

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)
        self.assertEqual(report2['formData'], json.loads(self.report3.form_data))

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)
        self.assertEqual(report3['formData'], json.loads(self.report1.form_data))
    '''
    def test_api_report_search_will_return_report_that_area_is_child_of_permitted_administration_area(self):
        area = self.area1.add_child(name='Namsan', location=self.area1.location)
        report = factory.create_report(type=self.type1, administration_area=area,
            date=datetime.datetime(2014, 10, 9, 13, 30, 45))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 4)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

        report4 = response_json['results'][3]
        self.assertEqual(report4['id'], report.id)

    def test_api_report_search_will_return_report_that_area_is_child_of_permitted_administration_area_with_authority(self):
        area = self.area1.add_child(name='Namsan', location=self.area1.location)
        report = factory.create_report(type=self.type1, administration_area=area,
            date=datetime.datetime(2014, 10, 9, 13, 30, 45))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 4)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

        report4 = response_json['results'][3]
        self.assertEqual(report4['id'], report.id)
    '''
    def test_api_report_search_by_user(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': 'createdBy:%s' % self.taeyeon.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report1.id)

    def test_api_report_search_by_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': 'type:%s' % self.type2.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

    def test_api_report_search_by_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': 'administrationArea:%s' % self.area1.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

    def test_api_report_search_by_form_data(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': u'symptom:ปวดหัว',
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

        response = self.client.get(reverse('reports_search'), {
            'q': 'symptom:fever',
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_search_by_form_data_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': u'symptom:ปวดหัว',
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

        response = self.client.get(reverse('reports_search'), {
            'q': 'symptom:fever',
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_search_multiple_value_in_one_field(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': u'symptom:ปวดหัว OR symptom:fever',
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

    def test_api_report_search_multiple_value_in_one_field_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': u'symptom:ปวดหัว OR symptom:fever',
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 3)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

        report3 = response_json['results'][2]
        self.assertEqual(report3['id'], self.report1.id)

    def test_api_report_search_greater_than_value(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': 'sickCount:[5 TO *]',
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

    def test_api_report_search_greater_than_value_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': 'sickCount:[5 TO *]',
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

    def test_api_report_search_multiple_data(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=symptom:fever AND createdBy:%s AND type:%s AND administrationArea:%s' % (
                self.taeyeon.id,
                self.type1.id,
                self.area1.id,
            ))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

    def test_api_report_search_multiple_data_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=symptom:fever AND createdBy:%s AND type:%s AND administrationArea:%s' % (
                self.taeyeon.id,
                self.type1.id,
                self.area1.id,
            ))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

    def test_api_report_search_results_only_have_permission_on_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': 'type:%s' % self.type3.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 0)

    def test_api_report_search_results_only_have_permission_on_report_type_with_authorit(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': 'type:%s' % self.type3.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 0)

    def test_api_report_search_results_only_have_permission_on_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': 'administrationArea:%s' % self.area3.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 0)

    def test_api_report_search_results_only_have_permission_on_administration_area_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search'), {
            'q': 'administrationArea:%s' % self.area3.id
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 0)

    def test_api_report_search_will_always_return_report_type_0(self):
        default_positive_type = ReportType.objects.get(id=0)
        factory.create_report(type=default_positive_type, administration_area=self.area1, negative=False)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 4)
    '''
    def test_api_report_search_will_always_return_report_type_0_with_authority(self):
        try:
            default_positive_type = ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            default_positive_type = ReportType.objects.create(id=0, code='positive-report', name='positive report')

        factory.create_report(type=default_positive_type, administration_area=self.area1, negative=False)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 4)
    '''
    def test_api_report_search_date_today(self):
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        yesterday = today - datetime.timedelta(days=1)

        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(today, datetime.time(0, 0)))
        report2 = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(tomorrow, datetime.time(0, 0)))
        report3 = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(yesterday, datetime.time(23, 59)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: today')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_date_today_with_authority(self):
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        yesterday = today - datetime.timedelta(days=1)

        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(today, datetime.time(0, 0)))
        report2 = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(tomorrow, datetime.time(0, 0)))
        report3 = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(yesterday, datetime.time(23, 59)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: today')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_date_yesterday(self):
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=yesterday)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: yesterday')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_date_yesterday_with_authority(self):
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=yesterday)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: yesterday')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_date_this_week(self):
        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.now())

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: this week')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_date_this_week_with_authority(self):
        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.now())

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: this week')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_last_7_days(self):
        last7days = datetime.datetime.now() - datetime.timedelta(days=7)
        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=last7days)

        last10days = datetime.datetime.now() - datetime.timedelta(days=10)
        report10 = factory.create_report(type=self.type1, administration_area=self.area1,
            date=last10days)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: last 7 days')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_last_7_days_with_authority(self):
        last7days = datetime.datetime.now() - datetime.timedelta(days=7)
        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=last7days)

        last10days = datetime.datetime.now() - datetime.timedelta(days=10)
        report10 = factory.create_report(type=self.type1, administration_area=self.area1,
            date=last10days)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: last 7 days')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_last_10_days(self):
        last7days = datetime.datetime.now() - datetime.timedelta(days=7)
        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=last7days)

        last10days = datetime.datetime.now() - datetime.timedelta(days=10)
        report10 = factory.create_report(type=self.type1, administration_area=self.area1,
            date=last10days)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: last 10 days')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], report10.id)

    def test_api_report_search_last_10_days_with_authority(self):
        last7days = datetime.datetime.now() - datetime.timedelta(days=7)
        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=last7days)

        last10days = datetime.datetime.now() - datetime.timedelta(days=10)
        report10 = factory.create_report(type=self.type1, administration_area=self.area1,
            date=last10days)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: last 10 days')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], report10.id)

    def test_api_report_search_date_today_timezone(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        report_today = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(today, datetime.time(20, 0)))
        report_yesterday = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(yesterday, datetime.time(20, 0)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: today')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report_yesterday.id)

    def test_api_report_search_date_today_timezone_with_authority(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        report_today = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(today, datetime.time(20, 0)))
        report_yesterday = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(yesterday, datetime.time(20, 0)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: today')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report_yesterday.id)

    def test_api_report_search_date_yesterday_timezone(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        last_2_day = today - datetime.timedelta(days=2)

        report_yesterday = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(yesterday, datetime.time(20, 0)))
        report_2_days_ago = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(last_2_day, datetime.time(20, 0)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: yesterday')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report_2_days_ago.id)

    def test_api_report_search_date_yesterday_timezone_with_authority(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        last_2_day = today - datetime.timedelta(days=2)

        report_yesterday = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(yesterday, datetime.time(20, 0)))
        report_2_days_ago = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(last_2_day, datetime.time(20, 0)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: yesterday')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report_2_days_ago.id)

    def test_api_report_search_date_this_week_timezone(self):
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())
        before_week_start = week_start - datetime.timedelta(days=1)

        report_before_week_start = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(before_week_start, datetime.time(22, 0)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: this week')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report_before_week_start.id)

    def test_api_report_search_date_this_week_timezone_with_authority(self):
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())
        before_week_start = week_start - datetime.timedelta(days=1)

        report_before_week_start = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(before_week_start, datetime.time(22, 0)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: this week')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report_before_week_start.id)

    def test_api_report_search_date_last_7_days_timezone(self):
        today = datetime.date.today()
        last8days = today - datetime.timedelta(days=8)

        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(last8days, datetime.time(20, 0)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: last 7 days')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_date_last_7_days_timezone_with_authority(self):
        today = datetime.date.today()
        last8days = today - datetime.timedelta(days=8)

        report = factory.create_report(type=self.type1, administration_area=self.area1,
            date=datetime.datetime.combine(last8days, datetime.time(20, 0)))

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: last 7 days')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], report.id)

    def test_api_report_search_date_date_range(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: [2014-11-09 TO 2014-11-11]')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_search_date_date_range_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: [2014-11-09 TO 2014-11-11]')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_search_date_date_range_timezone(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: [2014-11-09 TO 2014-11-11]')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_search_date_date_range_timezone_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: [2014-11-09 TO 2014-11-11]')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_search_date_datetime_range(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: [2014-11-09T12:00 TO 2014-11-11T15:00]')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_search_date_datetime_range_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=date: [2014-11-09T12:00 TO 2014-11-11T15:00]')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

        report2 = response_json['results'][1]
        self.assertEqual(report2['id'], self.report3.id)

    def test_api_report_search_date_datetime_range_timezone(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: [2014-11-09T12:00 TO 2014-11-11T15:00]')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report3.id)

    def test_api_report_search_date_datetime_range_timezone_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?tz=7&q=date: [2014-11-09T12:00 TO 2014-11-11T15:00]')
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report3.id)

    def test_api_report_search_area_name(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=area: %s' % self.area1.name)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

    def test_api_report_search_area_name_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=area: %s' % self.area1.name)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report2.id)

    def test_api_report_search_report_type_name(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=typeName: %s' % self.type2.name)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

    def test_api_report_search_report_type_name_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=typeName: %s' % self.type2.name)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report1.id)

    def test_api_report_search_report_created_by_name(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=createdByName: %s' % self.jessica.first_name)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report3.id)

        response = self.client.get(reverse('reports_search') + '?q=createdByName: %s' % self.jessica.last_name)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report3.id)

        response = self.client.get(reverse('reports_search') + '?q=createdByName: %s' % self.taeyeon.get_full_name())
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

    def test_api_report_search_report_created_by_name_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reports_search') + '?q=createdByName: %s' % self.jessica.first_name)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report3.id)

        response = self.client.get(reverse('reports_search') + '?q=createdByName: %s' % self.jessica.last_name)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 1)

        report1 = response_json['results'][0]
        self.assertEqual(report1['id'], self.report3.id)

        response = self.client.get(reverse('reports_search') + '?q=createdByName: %s' % self.taeyeon.get_full_name())
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['count'], 2)

    def test_anonymous_cannot_access_api_list_search(self):
        response = self.client.get(reverse('reports_search'))
        self.assertEqual(response.status_code, 401)


class TestApiReportTags(APITestCase):
    def setUp(self):

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)

        self.type = factory.create_report_type(authority=self.authority)
        self.area = factory.create_administration_area(authority=self.authority)

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=self.area, date=datetime.datetime(2014, 11, 7, 12, 30, 45))

        self.report2 = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=self.area, date=datetime.datetime(2014, 11, 11, 12, 30, 45))

    def test_anonymous_cannot_access_api_post_report_tags(self):
        params = {}
        response = self.client.post(reverse('add_reports_tags'), params)
        self.assertEqual(response.status_code, 401)

    def test_cannot_post_report_tags_without_data(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.taeyeon.auth_token.key)
        params = {}
        response = self.client.post(reverse('add_reports_tags'), params)
        self.assertEqual(response.status_code, 400)

    def test_cannot_post_report_tags_without_report_ids(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.taeyeon.auth_token.key)
        params = {
            'tags': [
                {'text': 'test'},
            ],
        }
        response = self.client.post(reverse('add_reports_tags'), params)
        self.assertEqual(response.status_code, 400)

    def test_cannot_post_report_tags_without_tags(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.taeyeon.auth_token.key)
        params = {
            'reportIds': [self.report1.id, self.report2.id]
        }
        response = self.client.post(reverse('add_reports_tags'), params)
        self.assertEqual(response.status_code, 400)

    def test_cannot_post_report_tags(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.taeyeon.auth_token.key)
        params = {
            'reportIds': [self.report1.id, self.report2.id],
            'tags': [
                {'text': 'test'},
            ],
        }
        response = self.client.post(reverse('add_reports_tags'), params)
        self.assertEqual(response.status_code, 200)

        report1 = Report.objects.get(id=self.report1.id)
        self.assertTrue("test" in report1.tags.values_list('name', flat=True))

        report2 = Report.objects.get(id=self.report2.id)
        self.assertTrue("test" in report2.tags.values_list('name', flat=True))

    def test_cannot_post_report_multiple_tags(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.taeyeon.auth_token.key)
        params = {
            'reportIds': [self.report1.id, self.report2.id],
            'tags': [
                {'text': 'test1'},
                {'text': 'test2'},
                {'text': 'test3'},
            ],
        }
        response = self.client.post(reverse('add_reports_tags'), params)
        self.assertEqual(response.status_code, 200)

        report1 = Report.objects.get(id=self.report1.id)
        self.assertTrue("test1" in report1.tags.values_list('name', flat=True))
        self.assertTrue("test2" in report1.tags.values_list('name', flat=True))
        self.assertTrue("test3" in report1.tags.values_list('name', flat=True))

        report2 = Report.objects.get(id=self.report2.id)
        self.assertTrue("test1" in report2.tags.values_list('name', flat=True))
        self.assertTrue("test2" in report2.tags.values_list('name', flat=True))
        self.assertTrue("test3" in report2.tags.values_list('name', flat=True))


class TestApiReportInvolved(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.yoona)

        self.type1 = factory.create_report_type(authority=self.authority)
        self.type2 = factory.create_report_type(authority=self.authority)
        self.type3 = factory.create_report_type()

        self.area1 = factory.create_administration_area(authority=self.authority)
        self.area2 = factory.create_administration_area(authority=self.authority)
        self.area3 = factory.create_administration_area()

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type2,
            administration_area=self.area1, date=datetime.datetime(2014, 11, 7, 12, 30, 45))
        self.report2 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area1, parent=self.report1,
            date=datetime.datetime(2014, 11, 9, 12, 30, 45))
        self.report3 = factory.create_report(created_by=self.jessica, type=self.type1,
            administration_area=self.area1, parent=self.report1,
            date=datetime.datetime(2014, 11, 11, 13, 30, 45))
        self.report4 = factory.create_report(type=self.type3, administration_area=self.area2)
        self.report5 = factory.create_report(type=self.type1, administration_area=self.area3)

    def test_api_report_involved_that_report_is_parent(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-involved', args=[self.report1.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        report1 = response_json[0]
        self.assertEqual(report1['id'], self.report3.id)
        self.assertEqual(report1['reportId'], self.report3.report_id)
        self.assertEqual(report1['guid'], self.report3.guid)
        self.assertEqual(report1['reportTypeId'], self.report3.type.id)
        self.assertEqual(report1['administrationAreaId'], self.report3.administration_area.id)
        self.assertEqual(report1['negative'], self.report3.negative)
        self.assertEqual(report1['createdByName'], self.report3.created_by.get_full_name())
        self.assertEqual(report1['date'], self.report3.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report1['incidentDate'], self.report3.incident_date.strftime('%Y-%m-%d'))

        report2 = response_json[1]
        self.assertEqual(report2['id'], self.report2.id)
        self.assertEqual(report2['reportId'], self.report2.report_id)
        self.assertEqual(report2['guid'], self.report2.guid)
        self.assertEqual(report2['reportTypeId'], self.report2.type.id)
        self.assertEqual(report2['administrationAreaId'], self.report2.administration_area.id)
        self.assertEqual(report2['negative'], self.report2.negative)
        self.assertEqual(report2['createdByName'], self.report2.created_by.get_full_name())
        self.assertEqual(report2['date'], self.report2.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report2['incidentDate'], self.report2.incident_date.strftime('%Y-%m-%d'))

    def test_api_report_involved_that_report_is_parent_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-involved', args=[self.report1.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        report1 = response_json[0]
        self.assertEqual(report1['id'], self.report3.id)
        self.assertEqual(report1['reportId'], self.report3.report_id)
        self.assertEqual(report1['guid'], self.report3.guid)
        self.assertEqual(report1['reportTypeId'], self.report3.type.id)
        self.assertEqual(report1['administrationAreaId'], self.report3.administration_area.id)
        self.assertEqual(report1['negative'], self.report3.negative)
        self.assertEqual(report1['createdByName'], self.report3.created_by.get_full_name())
        self.assertEqual(report1['date'], self.report3.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report1['incidentDate'], self.report3.incident_date.strftime('%Y-%m-%d'))

        report2 = response_json[1]
        self.assertEqual(report2['id'], self.report2.id)
        self.assertEqual(report2['reportId'], self.report2.report_id)
        self.assertEqual(report2['guid'], self.report2.guid)
        self.assertEqual(report2['reportTypeId'], self.report2.type.id)
        self.assertEqual(report2['administrationAreaId'], self.report2.administration_area.id)
        self.assertEqual(report2['negative'], self.report2.negative)
        self.assertEqual(report2['createdByName'], self.report2.created_by.get_full_name())
        self.assertEqual(report2['date'], self.report2.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report2['incidentDate'], self.report2.incident_date.strftime('%Y-%m-%d'))

    def test_api_report_involved_that_report_is_child(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-involved', args=[self.report2.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        report1 = response_json[0]
        self.assertEqual(report1['id'], self.report3.id)
        self.assertEqual(report1['reportId'], self.report3.report_id)
        self.assertEqual(report1['guid'], self.report3.guid)
        self.assertEqual(report1['reportTypeId'], self.report3.type.id)
        self.assertEqual(report1['administrationAreaId'], self.report3.administration_area.id)
        self.assertEqual(report1['negative'], self.report3.negative)
        self.assertEqual(report1['createdByName'], self.report3.created_by.get_full_name())
        self.assertEqual(report1['date'], self.report3.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report1['incidentDate'], self.report3.incident_date.strftime('%Y-%m-%d'))

        report2 = response_json[1]
        self.assertEqual(report2['id'], self.report1.id)
        self.assertEqual(report2['reportId'], self.report1.report_id)
        self.assertEqual(report2['guid'], self.report1.guid)
        self.assertEqual(report2['reportTypeId'], self.report1.type.id)
        self.assertEqual(report2['administrationAreaId'], self.report1.administration_area.id)
        self.assertEqual(report2['negative'], self.report1.negative)
        self.assertEqual(report2['createdByName'], self.report1.created_by.get_full_name())
        self.assertEqual(report2['date'], self.report1.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report2['incidentDate'], self.report1.incident_date.strftime('%Y-%m-%d'))

    def test_api_report_involved_that_report_is_child_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-involved', args=[self.report2.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        report1 = response_json[0]
        self.assertEqual(report1['id'], self.report3.id)
        self.assertEqual(report1['reportId'], self.report3.report_id)
        self.assertEqual(report1['guid'], self.report3.guid)
        self.assertEqual(report1['reportTypeId'], self.report3.type.id)
        self.assertEqual(report1['administrationAreaId'], self.report3.administration_area.id)
        self.assertEqual(report1['negative'], self.report3.negative)
        self.assertEqual(report1['createdByName'], self.report3.created_by.get_full_name())
        self.assertEqual(report1['date'], self.report3.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report1['incidentDate'], self.report3.incident_date.strftime('%Y-%m-%d'))

        report2 = response_json[1]
        self.assertEqual(report2['id'], self.report1.id)
        self.assertEqual(report2['reportId'], self.report1.report_id)
        self.assertEqual(report2['guid'], self.report1.guid)
        self.assertEqual(report2['reportTypeId'], self.report1.type.id)
        self.assertEqual(report2['administrationAreaId'], self.report1.administration_area.id)
        self.assertEqual(report2['negative'], self.report1.negative)
        self.assertEqual(report2['createdByName'], self.report1.created_by.get_full_name())
        self.assertEqual(report2['date'], self.report1.date.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(report2['incidentDate'], self.report1.incident_date.strftime('%Y-%m-%d'))

    def test_api_report_involved_results_only_have_permission_on_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-involved', args=[self.report4.id]))
        self.assertEqual(response.status_code, 403)

    def test_api_report_involved_results_only_have_permission_on_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-involved', args=[self.report5.id]))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_access_api_list_reports(self):
        response = self.client.get(reverse('report-involved', args=[self.report1.id]))
        self.assertEqual(response.status_code, 401)


class TestApiReportFollow(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.yoona)

        self.type1 = factory.create_report_type(authority=self.authority)
        self.type2 = factory.create_report_type(authority=self.authority)
        self.type3 = factory.create_report_type()

        self.area1 = factory.create_administration_area(authority=self.authority)
        self.area2 = factory.create_administration_area(authority=self.authority)
        self.area3 = factory.create_administration_area()

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type2,
            administration_area=self.area1, date=datetime.datetime(2014, 11, 7, 12, 30, 45))
        self.report2 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area1, date=datetime.datetime(2014, 11, 9, 12, 30, 45))
        self.report3 = factory.create_report(created_by=self.jessica, type=self.type1,
            administration_area=self.area1, date=datetime.datetime(2014, 11, 11, 13, 30, 45))
        self.report4 = factory.create_report(type=self.type3, administration_area=self.area2)
        self.report5 = factory.create_report(type=self.type1, administration_area=self.area3)

    def test_api_post_report_follow(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'parent': self.report2.id
        }
        response = self.client.post(reverse('report-follow', args=[self.report1.id]), params)
        self.assertEqual(response.status_code, 200)

        report1 = Report.objects.get(id=self.report1.id)
        self.assertEqual(report1.parent, self.report2)

        # CHECK CREATE REPORT COMMENT FLAG
        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, report1)
        self.assertEqual(comment.created_by, self.taeyeon)

        flag = Flag.objects.latest('id')
        self.assertEqual(flag.comment, comment)
        self.assertEqual(flag.priority, PRIORITY_FOLLOW)
        self.assertEqual(flag.flag_owner, self.taeyeon)

    def test_api_post_report_follow_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            'parent': self.report2.id
        }
        response = self.client.post(reverse('report-follow', args=[self.report1.id]), params)
        self.assertEqual(response.status_code, 200)

        report1 = Report.objects.get(id=self.report1.id)
        self.assertEqual(report1.parent, self.report2)

        # CHECK CREATE REPORT COMMENT FLAG
        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, report1)
        self.assertEqual(comment.created_by, self.yoona)

        flag = Flag.objects.latest('id')
        self.assertEqual(flag.comment, comment)
        self.assertEqual(flag.priority, PRIORITY_FOLLOW)
        self.assertEqual(flag.flag_owner, self.yoona)

    def test_api_post_report_follow_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.post(reverse('report-follow', args=[self.report1.id]))
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['parent'], 'This field is required.')

        params = {
            'parent': 12345,
        }
        response = self.client.post(reverse('report-follow', args=[self.report1.id]), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['parent'], 'Report not found.')
    '''
    def test_api_post_report_follow_only_have_permission_on_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.post(reverse('report-follow', args=[self.report4.id]))
        self.assertEqual(response.status_code, 403)
    '''

    def test_api_post_report_follow_only_have_permission_on_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.post(reverse('report-follow', args=[self.report5.id]))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_access_api_post_report_follow(self):
        response = self.client.post(reverse('report-follow', args=[self.report1.id]))
        self.assertEqual(response.status_code, 401)

    def test_cannot_get_api_post_report_follow(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-follow', args=[self.report1.id]))
        self.assertEqual(response.status_code, 405)


class TestApiReportCreate(APITestCase):
    def setUp(self):

        try:
            self.default_positive_type = ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            self.default_positive_type = ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )
            
        call_command('log_action_create', interactive=False, verbosity=0)
        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user(administration_area=factory.create_administration_area())
        self.jessica = factory.create_user()
        self.yoona = factory.create_user(is_superuser=True, is_staff=True)
        self.krystal = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.krystal)

        self.type = factory.create_report_type(authority=self.authority)

        self.area = factory.create_administration_area(authority=self.authority)
        self.area2 = factory.create_administration_area(authority=self.authority)

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=self.area, date=datetime.datetime(2014, 11, 7, 12, 30, 45))
        self.report2 = factory.create_report(created_by=self.krystal, type=self.type,
            administration_area=self.area, date=datetime.datetime(2014, 11, 7, 12, 30, 45))

    def test_post_api_report_create(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain",
                "sickCount": 4,
                "deathCount": 3,
                "totalCount": 12,
                "nearByCount": 3
            },
            "negative": True,
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 100.7522060000000010
            }
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(minutes=420)

        report = Report.objects.latest('id')
        self.assertEqual(report.report_id, 123)
        self.assertEqual(report.guid, '09d09djjjkdf09df0dfdfdfdf')
        self.assertEqual(report.type, self.type)
        self.assertEqual(report.date, datetime.datetime(2014, 9, 1, 4, 11, 15, tzinfo=TZ()))
        self.assertEqual(report.incident_date, datetime.date(2014, 9, 1))
        self.assertEqual(report.administration_area, self.area)
        self.assertEqual(report.administration_location.wkt, self.area.location.wkt)
        self.assertEqual(report.remark, 'xxxxxxxxxxxxxx')
        self.assertEqual(report.negative, True)
        self.assertEqual(report.report_location.wkt, 'POINT (100.7522060000000010 13.8082770000000004)')
        self.assertEqual(json.loads(report.form_data), {
            "animalType": "dog",
            "symptom": "cough,fever,pain",
            "sickCount": 4,
            "deathCount": 3,
            "totalCount": 12,
            "nearByCount": 3
        })
        self.assertEqual(report.created_by, self.taeyeon)

    def test_post_api_report_create_with_report_type_code(self):
        """Use report type code instead of report type id"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": 10001,
            "guid": "guid-1001",
            "reportTypeCode": self.type.code,
            "date": timezone.now(),
            "incidentDate": timezone.now().strftime('%Y-%m-%d'),
            "administrationAreaId": self.area.id,
            "formData": {},
            "negative": True
        }

        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        created_report = Report.objects.latest('id')
        self.assertEqual(created_report.type.id, self.type.id)


    def test_post_api_report_create_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain",
                "sickCount": 4,
                "deathCount": 3,
                "totalCount": 12,
                "nearByCount": 3
            },
            "negative": True,
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 100.7522060000000010
            }
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(minutes=420)

        report = Report.objects.latest('id')
        self.assertEqual(report.report_id, 123)
        self.assertEqual(report.guid, '09d09djjjkdf09df0dfdfdfdf')
        self.assertEqual(report.type, self.type)
        self.assertEqual(report.date, datetime.datetime(2014, 9, 1, 4, 11, 15, tzinfo=TZ()))
        self.assertEqual(report.incident_date, datetime.date(2014, 9, 1))
        self.assertEqual(report.administration_area, self.area)
        self.assertEqual(report.administration_location.wkt, self.area.location.wkt)
        self.assertEqual(report.remark, 'xxxxxxxxxxxxxx')
        self.assertEqual(report.negative, True)
        self.assertEqual(report.report_location.wkt, 'POINT (100.7522060000000010 13.8082770000000004)')
        self.assertEqual(json.loads(report.form_data), {
            "animalType": "dog",
            "symptom": "cough,fever,pain",
            "sickCount": 4,
            "deathCount": 3,
            "totalCount": 12,
            "nearByCount": 3
        })
        self.assertEqual(report.created_by, self.krystal)

    def test_post_api_follow_report_create_by_parent_guid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain",
                "sickCount": 4,
                "deathCount": 3,
                "totalCount": 12,
                "nearByCount": 3
            },
            "negative": True,
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 100.7522060000000010
            },
            "parentGuid": self.report1.guid
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        # response_json = json.loads(response.content)
        # self.assertTrue(response_json['id'])
        # self.assertEqual(response_json['reportId'], 123)
        # self.assertEqual(response_json['guid'], '09d09djjjkdf09df0dfdfdfdf')
        # self.assertEqual(response_json['reportTypeId'], self.type.id)
        # self.assertEqual(response_json['date'], '2014-09-01T04:11:15+07:00')
        # self.assertEqual(response_json['incidentDate'], '2014-09-01')
        # self.assertEqual(response_json['administrationAreaId'], self.area.id)
        # self.assertEqual(response_json['remark'], 'xxxxxxxxxxxxxx')
        # self.assertEqual(response_json['negative'], True)
        # self.assertEqual(response_json['reportLocation']['type'], 'Point')
        # self.assertEqual(response_json['reportLocation']['coordinates'], [100.7522060000000010, 13.8082770000000004])
        # self.assertEqual(response_json['formData'], {
        #     "animalType": "dog",
        #     "symptom": "cough,fever,pain",
        #     "sickCount": 4,
        #     "deathCount": 3,
        #     "totalCount": 12,
        #     "nearByCount": 3
        # })
        # self.assertEqual(response_json['createdBy'], self.taeyeon.get_full_name())

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(minutes=420)

        report = Report.objects.latest('id')
        self.assertEqual(report.report_id, 123)
        self.assertEqual(report.guid, '09d09djjjkdf09df0dfdfdfdf')
        self.assertEqual(report.type, self.type)
        self.assertEqual(report.date, datetime.datetime(2014, 9, 1, 4, 11, 15, tzinfo=TZ()))
        self.assertEqual(report.incident_date, datetime.date(2014, 9, 1))
        self.assertEqual(report.administration_area, self.area)
        self.assertEqual(report.administration_location.wkt, self.area.location.wkt)
        self.assertEqual(report.remark, 'xxxxxxxxxxxxxx')
        self.assertEqual(report.negative, True)
        self.assertEqual(report.report_location.wkt, 'POINT (100.7522060000000010 13.8082770000000004)')
        self.assertEqual(report.parent, self.report1)
        # self.assertEqual(report.priority, PRIORITY_FOLLOW)
        self.assertEqual(json.loads(report.form_data), {
            "animalType": "dog",
            "symptom": "cough,fever,pain",
            "sickCount": 4,
            "deathCount": 3,
            "totalCount": 12,
            "nearByCount": 3
        })
        self.assertEqual(report.created_by, self.taeyeon)

    def test_post_api_follow_report_create_by_parent_guid_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain",
                "sickCount": 4,
                "deathCount": 3,
                "totalCount": 12,
                "nearByCount": 3
            },
            "negative": True,
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 100.7522060000000010
            },
            "parentGuid": self.report2.guid
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(minutes=420)

        report = Report.objects.latest('id')
        self.assertEqual(report.report_id, 123)
        self.assertEqual(report.guid, '09d09djjjkdf09df0dfdfdfdf')
        self.assertEqual(report.type, self.type)
        self.assertEqual(report.date, datetime.datetime(2014, 9, 1, 4, 11, 15, tzinfo=TZ()))
        self.assertEqual(report.incident_date, datetime.date(2014, 9, 1))
        self.assertEqual(report.administration_area, self.area)
        self.assertEqual(report.administration_location.wkt, self.area.location.wkt)
        self.assertEqual(report.remark, 'xxxxxxxxxxxxxx')
        self.assertEqual(report.negative, True)
        self.assertEqual(report.report_location.wkt, 'POINT (100.7522060000000010 13.8082770000000004)')
        self.assertEqual(json.loads(report.form_data), {
            "animalType": "dog",
            "symptom": "cough,fever,pain",
            "sickCount": 4,
            "deathCount": 3,
            "totalCount": 12,
            "nearByCount": 3
        })
        self.assertEqual(report.parent, self.report2)
        # self.assertEqual(report.priority, PRIORITY_FOLLOW)
        self.assertEqual(report.created_by, self.krystal)

    def test_post_api_report_create_date_with_multiple_format(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        # FORMAT +0700
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+0700",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "formData": {
                "animalType": "dog",
            },
            "negative": False,
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        # response_json = json.loads(response.content)
        # self.assertEqual(response_json['date'], '2014-09-01T04:11:15+07:00')

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(minutes=420)

        report = Report.objects.latest('id')
        self.assertEqual(report.date, datetime.datetime(2014, 9, 1, 4, 11, 15, tzinfo=TZ()))

        # FORMAT Z
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0zczczczc",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15Z",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "formData": {
                "animalType": "dog",
            },
            "negative": False,
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        # response_json = json.loads(response.content)
        # self.assertEqual(response_json['date'], '2014-09-01T04:11:15+00:00')

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(0)

        report = Report.objects.latest('id')
        self.assertEqual(report.date, datetime.datetime(2014, 9, 1, 4, 11, 15, tzinfo=TZ()))

    def test_post_api_report_create_date_with_multiple_format_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        # FORMAT +0700
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+0700",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "formData": {
                "animalType": "dog",
            },
            "negative": False,
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(minutes=420)

        report = Report.objects.latest('id')
        self.assertEqual(report.date, datetime.datetime(2014, 9, 1, 4, 11, 15, tzinfo=TZ()))

        # FORMAT Z
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0zczczczc",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15Z",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "formData": {
                "animalType": "dog",
            },
            "negative": False,
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(0)

        report = Report.objects.latest('id')
        self.assertEqual(report.date, datetime.datetime(2014, 9, 1, 4, 11, 15, tzinfo=TZ()))

    '''
    def test_post_api_report_create_positive_report_type_and_area_0(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": 0,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            # "administrationAreaId": 0,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {},
            "negative": False,
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 100.7522060000000010
            }
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

    def test_post_api_report_create_positive_report_type_and_area_0_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": 0,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            # "administrationAreaId": 0,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {},
            "negative": False,
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 100.7522060000000010
            }
        }
        response = self.client.post(reverse('report-list'), params)
        print response
        self.assertEqual(response.status_code, 201)

    def test_post_api_report_create_positive_report_type_and_area_0_and_reporter_does_not_have_default_area_will_error(self):
        self.yoontae = factory.create_user()

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoontae.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": 0,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            # "administrationAreaId": 0,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {},
            "negative": False,
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 100.7522060000000010
            }
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['administrationAreaId'], ['This user does not have default admintration area.'])
    '''

    def test_cannot_post_api_report_if_user_dont_have_authorized_in_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        params = {
            "reportTypeId": self.type.id,
            "reportId": 1234,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportTypeId'], ['You do not have permission to create this report type.'])

    def test_cannot_post_api_report_if_user_dont_have_authorized_in_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        params = {
            "administrationAreaId": self.area.id,
            "reportId": 1234,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['administrationAreaId'], ['You do not have permission to create this area.'])

    def test_cannot_post_api_report_if_administration_area_group_is_not_role_reporter(self):
        group_a = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)
        area = factory.create_administration_area()
        factory.create_group_administration_area(group=group_a, administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain",
                "sickCount": 4,
                "deathCount": 3,
                "totalCount": 12,
                "nearByCount": 3
            },
            "negative": True,
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 100.7522060000000010
            }
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['administrationAreaId'], ['You do not have permission to create this area.'])

    def test_cannot_post_api_report_if_report_type_group_is_not_role_reporter(self):
        group_r = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE)
        newtype = factory.create_report_type()
        factory.create_group_report_type(group=group_r, report_type=newtype)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": newtype.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain",
                "sickCount": 4,
                "deathCount": 3,
                "totalCount": 12,
                "nearByCount": 3
            },
            "negative": True,
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 100.7522060000000010
            }
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportTypeId'], ['You do not have permission to create this report type.'])
    '''
    def test_post_api_report_on_area_that_child_of_permitted_administration_area(self):
        area = self.area.add_child(name='Namsan', location=self.area.location)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain",
            },
            "negative": True
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

        # response_json = json.loads(response.content)
        # self.assertTrue(response_json['id'])

    def test_post_api_report_on_area_that_child_of_permitted_administration_area_with_authority(self):
        area = self.area.add_child(name='Namsan', location=self.area.location)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain",
            },
            "negative": True
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)
    '''
    def test_staff_can_post_api_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain"
            },
            "negative": True,
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 201)

    def test_report_guid_must_be_unique(self):
        report = factory.create_report()
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": 123,
            "guid": report.guid,
            "reportTypeId": self.type.id,
            "date": "2014-09-01T04:11:15+07:00",
            "incidentDate": "2014-09-01",
            "administrationAreaId": self.area.id,
            "remark": "xxxxxxxxxxxxxx",
            "formData": {
                "animalType": "dog",
                "symptom": "cough,fever,pain",
                "sickCount": 4,
                "deathCount": 3,
                "totalCount": 12,
                "nearByCount": 3
            },
            "negative": True,
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['guid'], ['Report with this Guid already exists.'])

    def test_report_location_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportLocation": {
                "lat": 13.8082770000000004,
                "lng": 100.7522060000000010
            }
        }

        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportLocation'], ['Invalid format.'])

        # INVALID LATITUDE
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportLocation": {
                "latitude": 13.8082770000000004,
                "longitude": 190.7522060000000010
            }
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportLocation'], [u'Longitude must be in between -180 to 180 degree.'])

        # INVALID LONGITUDE
        params = {
            "reportId": 123,
            "guid": "09d09djjjkdf09df0dfdfdfdf",
            "reportLocation": {
                "latitude": -91.8082770000000004,
                "longitude": 100.7522060000000010
            }
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportLocation'], ['Latitude must be in between -90 to 90 degree.'])

    def test_post_api_report_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'negative': True
        }
        response = self.client.post(reverse('report-list'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], ['This field is required.'])

    def test_anonymous_cannot_access_api_report_create(self):
        response = self.client.post(reverse('report-list'))
        self.assertEqual(response.status_code, 401)


class TestApiReport(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user(is_superuser=True, is_staff=True)
        self.krystal = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.krystal)

        self.type1 = factory.create_report_type(authority=self.authority)
        self.type2 = factory.create_report_type(authority=self.authority)

        self.area1 = factory.create_administration_area(authority=self.authority)
        self.area2 = factory.create_administration_area(authority=self.authority)

        self.report1 = factory.create_report(type=self.type1, administration_area=self.area1)
        self.report2 = factory.create_report(type=self.type2, administration_area=self.area2)

    def test_api_get_report(self):
        image = factory.create_report_image(report=self.report1)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-detail', args=[self.report1.id]))

        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], self.report1.id)
        self.assertEqual(response_json['reportId'], self.report1.report_id)
        self.assertEqual(response_json['guid'], self.report1.guid)
        self.assertEqual(response_json['reportTypeId'], self.report1.type.id)
        self.assertEqual(response_json['reportTypeName'], self.report1.type.name)
        self.assertEqual(response_json['date'], self.report1.date.isoformat() + '+00:00')
        self.assertEqual(response_json['incidentDate'], self.report1.incident_date.strftime('%Y-%m-%d'))
        self.assertEqual(response_json['administrationAreaId'], self.report1.administration_area.id)
        # self.assertEqual(response_json['remark'], self.report1.remark)
        self.assertEqual(response_json['negative'], self.report1.negative)
        self.assertEqual(response_json['formData'], json.loads(self.report1.form_data))
        self.assertEqual(response_json['images'][0]['imageUrl'], image.image_url)
        self.assertEqual(response_json['images'][0]['thumbnailUrl'], image.thumbnail_url)
        self.assertEqual(response_json['images'][0]['note'], image.note)
        self.assertEqual(response_json['createdBy'], self.report1.created_by.get_full_name())
        self.assertEqual(response_json['createdByContact'], self.report1.created_by.contact)

    def test_api_get_report_with_authority(self):
        image = factory.create_report_image(report=self.report1)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('report-detail', args=[self.report1.id]))

        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], self.report1.id)
        self.assertEqual(response_json['reportId'], self.report1.report_id)
        self.assertEqual(response_json['guid'], self.report1.guid)
        self.assertEqual(response_json['reportTypeId'], self.report1.type.id)
        self.assertEqual(response_json['reportTypeName'], self.report1.type.name)
        self.assertEqual(response_json['date'], self.report1.date.isoformat() + '+00:00')
        self.assertEqual(response_json['incidentDate'], self.report1.incident_date.strftime('%Y-%m-%d'))
        self.assertEqual(response_json['administrationAreaId'], self.report1.administration_area.id)
        # self.assertEqual(response_json['remark'], self.report1.remark)
        self.assertEqual(response_json['negative'], self.report1.negative)
        self.assertEqual(response_json['formData'], json.loads(self.report1.form_data))
        self.assertEqual(response_json['images'][0]['imageUrl'], image.image_url)
        self.assertEqual(response_json['images'][0]['thumbnailUrl'], image.thumbnail_url)
        self.assertEqual(response_json['images'][0]['note'], image.note)
        self.assertEqual(response_json['createdBy'], self.report1.created_by.get_full_name())
        self.assertEqual(response_json['createdByContact'], self.report1.created_by.contact)

    def test_cannot_get_api_get_report_if_user_dont_have_authorized_on_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('report-detail', args=[self.report1.id]))
        self.assertEqual(response.status_code, 403)
    '''
    def test_api_get_report_that_area_is_child_of_permitted_administration_area(self):
        area = self.area1.add_child(name='Namsan', location=self.area1.location)
        report = factory.create_report(type=self.type1, administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-detail', args=[report.id]))

        self.assertEqual(response.status_code, 403)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], report.id)

    def test_api_get_report_that_area_is_child_of_permitted_administration_area_with_authority(self):
        area = self.area1.add_child(name='Namsan', location=self.area1.location)
        report = factory.create_report(type=self.type1, administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('report-detail', args=[report.id]))

        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], report.id)
    '''
    def test_cannot_get_api_get_report_if_user_dont_have_authorized_on_adminstration_area(self):
        group_r = factory.add_user_to_new_group_type_report_type(user=self.jessica)
        factory.create_group_report_type(group=group_r, report_type=self.type1)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('report-detail', args=[self.report1.id]))
        self.assertEqual(response.status_code, 403)

    def test_cannot_get_api_get_report_that_administration_area_group_is_not_has_role_reporter(self):
        group_a = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)
        area = factory.create_administration_area()
        factory.create_group_administration_area(group=group_a, administration_area=area)

        report = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-detail', args=[report.id]))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_get_api_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('report-detail', args=[self.report1.id]))
        self.assertEqual(response.status_code, 200)

    def test_cannot_get_api_get_report_if_not_exists(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('report-detail', args=[self.report1.id+1000000]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_cannot_access_api_get_report(self):
        response = self.client.get(reverse('report-detail', args=[self.report1.id]))
        self.assertEqual(response.status_code, 401)


@patch('django_redis.get_redis_connection', mock_strict_redis_client)
class TestApiReportTypeList(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0
            )

        call_command('clear_index', interactive=False, verbosity=0)
        call_command('clear_graph', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user()
        self.minah = factory.create_user(is_superuser=True, is_staff=True)
        self.krystal = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.krystal)

        self.authority_1 = factory.create_authority()
        self.authority_1.users.add(self.taeyeon)

        self.authority_2 = factory.create_authority()
        self.authority_2.users.add(self.jessica)

        self.type1 = factory.create_report_type(name='VX-2014', authority=self.authority)
        self.type2 = factory.create_report_type(name='Human', authority=self.authority)
        self.type3 = factory.create_report_type(name='Animal', authority=self.authority_2)

        self.authority_1.inherits.add(self.authority)
        self.authority_1.inherits.add(self.authority_2)

    def test_api_list_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reporttype-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

        type1 = response_json[0]
        self.assertEqual(type1['id'], self.type1.id)
        self.assertEqual(type1['name'], self.type1.name)
        self.assertEqual(type1['version'], self.type1.version)
        self.assertFalse(type1.has_key('definition'))

        type2 = response_json[1]
        self.assertEqual(type2['id'], self.type2.id)
        self.assertEqual(type2['name'], self.type2.name)
        self.assertEqual(type2['version'], self.type2.version)

        type3 = response_json[2]
        self.assertEqual(type3['id'], self.type3.id)
        self.assertEqual(type3['name'], self.type3.name)
        self.assertEqual(type3['version'], self.type3.version)

    def test_api_list_report_type_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('reporttype-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        type1 = response_json[0]
        self.assertEqual(type1['id'], self.type1.id)
        self.assertEqual(type1['name'], self.type1.name)
        self.assertEqual(type1['version'], self.type1.version)
        self.assertFalse(type1.has_key('definition'))

        type2 = response_json[1]
        self.assertEqual(type2['id'], self.type2.id)
        self.assertEqual(type2['name'], self.type2.name)
        self.assertEqual(type2['version'], self.type2.version)

    def test_api_list_report_type_only_has_permission_on_those_report_types(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('reporttype-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        type1 = response_json[0]
        self.assertEqual(type1['id'], self.type3.id)
        self.assertEqual(type1['name'], self.type3.name)
        self.assertEqual(type1['version'], self.type3.version)

    def test_api_list_report_type_only_group_has_role_reporter(self):
        group_r = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE)
        newtype = factory.create_report_type()
        factory.create_group_report_type(group=group_r, report_type=newtype)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reporttype-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

    def test_api_list_report_type_return_empty_list_if_not_have_any_permission(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reporttype-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 0)

    def test_staff_can_get_all_api_list_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.minah.auth_token.key)
        response = self.client.get(reverse('reporttype-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

    def test_anonymous_cannot_access_api_list_reports(self):
        response = self.client.get(reverse('reporttype-list'))
        self.assertEqual(response.status_code, 401)


@patch('django_redis.get_redis_connection', mock_strict_redis_client)
class TestApiReportType(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user(is_staff=True, is_superuser=True)
        self.krystal = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.krystal)

        self.type1 = factory.create_report_type(authority=self.authority)
        self.type2 = factory.create_report_type(authority=self.authority)

    def test_api_get_report_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reporttype-detail', args=[self.type1.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], self.type1.id)
        self.assertEqual(response_json['name'], self.type1.name)
        self.assertEqual(response_json['version'], self.type1.version)
        self.assertEqual(response_json['template'], self.type1.template)
        self.assertEqual(response_json['definition'], json.loads(self.type1.form_definition))

    def test_api_get_report_type_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('reporttype-detail', args=[self.type1.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], self.type1.id)
        self.assertEqual(response_json['name'], self.type1.name)
        self.assertEqual(response_json['version'], self.type1.version)
        self.assertEqual(response_json['template'], self.type1.template)
        self.assertEqual(response_json['definition'], json.loads(self.type1.form_definition))

    def test_cannot_get_api_get_report_type_if_user_dont_have_authorized(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('reporttype-detail', args=[self.type1.id]))
        self.assertEqual(response.status_code, 403)

    def test_cannot_get_api_get_report_type_if_group_is_not_has_role_reporter(self):
        group_r = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE)
        newtype = factory.create_report_type()
        factory.create_group_report_type(group=group_r, report_type=newtype)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reporttype-detail', args=[newtype.id]))
        self.assertEqual(response.status_code, 403)

    def test_cannot_get_api_get_report_type_if_not_exists(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('reporttype-detail', args=[self.type1.id+100]))
        self.assertEqual(response.status_code, 404)

    def test_staff_can_get_api_get_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('reporttype-detail', args=[self.type1.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_cannot_access_api_get_reports(self):
        response = self.client.get(reverse('reporttype-detail', args=[self.type1.id]))
        self.assertEqual(response.status_code, 401)


class TestApiReportImageCreate(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()

        self.report = factory.create_report(created_by=self.taeyeon)

    def test_post_api_report_image(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        imageUrl = 'https://s3-ap-southeast-1.amazonaws.com/podd/fe97493f-fef7-4e8e-9b97-a179c43bd5fa'
        params = {
            "reportGuid": self.report.guid,
            "guid": "dfdfdf0003434300343",
            "imageUrl": imageUrl,
            "thumbnailUrl": imageUrl,
            "note": "fever",
            "location": 'POINT(100.7522060000000010 13.8082770000000004)'
        }
        response = self.client.post(reverse('add_report_image'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['guid'], 'dfdfdf0003434300343')
        self.assertEqual(response_json['imageUrl'], imageUrl)
        self.assertEqual(response_json['thumbnailUrl'], imageUrl)
        self.assertEqual(response_json['note'], 'fever')
        self.assertEqual(response_json['location']['latitude'], 13.8082770000000004)
        self.assertEqual(response_json['location']['longitude'], 100.7522060000000010)


        image = ReportImage.objects.latest('id')
        self.assertEqual(image.report, self.report)
        self.assertEqual(image.guid, 'dfdfdf0003434300343')
        self.assertEqual(image.image_url, imageUrl)
        self.assertEqual(image.thumbnail_url, imageUrl)
        self.assertEqual(image.note, 'fever')

    def test_post_api_report_image_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.post(reverse('add_report_image'))
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportGuid'], 'Report is not found.')

        params = {
            "reportGuid": self.report.guid,
        }
        response = self.client.post(reverse('add_report_image'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['guid'], ['This field is required.'])
        self.assertEqual(response_json['imageUrl'], ['This field is required.'])
        self.assertEqual(response_json['thumbnailUrl'], ['This field is required.'])

    def test_anonymous_cannot_access_api_report_image_create(self):
        response = self.client.post(reverse('add_report_image'))
        self.assertEqual(response.status_code, 401)


class TestApiReportImageUpload(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()

        # get_temporary_file()

    @patch('reports.api.upload_to_s3', mock_upload_to_s3)
    def test_post_image_upload(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        m = mock_open()
        with patch('__main__.open', m, create=True):
            send_file = open('/tmp/hello.world.jpg', 'r')

        params = {
            'image': send_file,
        }

        content = encode_multipart('BoUnDaRyStRiNg', params)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

        response = self.client.post(reverse('upload_report_image'), content, content_type=content_type)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['imageUrl'], 'hello.world.jpg')
        self.assertEqual(response_json['thumbnailUrl'], 'hello.world-thumbnail.jpg')

    def test_cannot_get_upload_report_image(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('upload_report_image'))
        self.assertEqual(response.status_code, 405)

    def test_anonymous_cannot_post_upload_report_image(self):
        response = self.client.post(reverse('upload_report_image'))
        self.assertEqual(response.status_code, 401)


class TestApiReportComment(APITestCase):
    def setUp(self):
        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user()
        self.krystal = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.krystal)

        self.type = factory.create_report_type(authority=self.authority)
        self.area = factory.create_administration_area(authority=self.authority)

        self.report = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=self.area)

    def test_post_api_report_comment_by_report_without_file(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "message": "Hello baby",
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello baby')
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')
        self.assertEqual(comment.file_url, None)
        self.assertEqual(comment.created_by, self.taeyeon)

    def test_post_api_report_comment_by_report_without_file_and_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "message": "Hello baby",
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello baby')
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')
        self.assertEqual(comment.file_url, None)
        self.assertEqual(comment.created_by, self.krystal)

    def test_post_api_report_comment_by_report_comment_without_file(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello baby",
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello baby')
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')
        self.assertEqual(comment.file_url, None)
        self.assertEqual(comment.created_by, self.taeyeon)

    def test_post_api_report_comment_by_report_comment_without_file_and_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello baby",
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello baby')
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')
        self.assertEqual(comment.file_url, None)
        self.assertEqual(comment.created_by, self.krystal)

    @patch('reports.api.upload_to_s3', mock_upload_to_s3)
    def test_post_api_report_comment_by_report_with_file(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        m = mock_open()
        with patch('__main__.open', m, create=True):
            send_file = open('/tmp/hello.world.jpg', 'r')
        params = {
            "message": "Hello baby",
            "file": send_file,
        }
        content = encode_multipart('BoUnDaRyStRiNg', params)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

        response = self.client.post(reverse('report-comment', args=[self.report.id]), content, content_type=content_type)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello baby')
        self.assertEqual(response_json['fileUrl'], 'hello.world.jpg')

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')
        self.assertEqual(comment.file_url, 'hello.world.jpg')
        self.assertEqual(comment.created_by, self.taeyeon)

    @patch('reports.api.upload_to_s3', mock_upload_to_s3)
    def test_post_api_report_comment_by_report_with_file_and_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        m = mock_open()
        with patch('__main__.open', m, create=True):
            send_file = open('/tmp/hello.world.jpg', 'r')
        params = {
            "message": "Hello baby",
            "file": send_file,
        }
        content = encode_multipart('BoUnDaRyStRiNg', params)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

        response = self.client.post(reverse('report-comment', args=[self.report.id]), content, content_type=content_type)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello baby')
        self.assertEqual(response_json['fileUrl'], 'hello.world.jpg')

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')
        self.assertEqual(comment.file_url, 'hello.world.jpg')
        self.assertEqual(comment.created_by, self.krystal)

    @patch('reports.api.upload_to_s3', mock_upload_to_s3)
    def test_post_api_report_comment_by_report_comment_with_file(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        m = mock_open()
        with patch('__main__.open', m, create=True):
            send_file = open('/tmp/hello.world.jpg', 'r')
        params = {
            "reportId": self.report.id,
            "message": "Hello baby",
            "file": send_file,
        }
        content = encode_multipart('BoUnDaRyStRiNg', params)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

        response = self.client.post(reverse('reportcomment-list'), content, content_type=content_type)
        send_file.closed
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello baby')
        self.assertEqual(response_json['fileUrl'], 'hello.world.jpg')

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')
        self.assertEqual(comment.file_url, 'hello.world.jpg')
        self.assertEqual(comment.created_by, self.taeyeon)

    @patch('reports.api.upload_to_s3', mock_upload_to_s3)
    def test_post_api_report_comment_by_report_comment_with_file_and_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        m = mock_open()
        with patch('__main__.open', m, create=True):
            send_file = open('/tmp/hello.world.jpg', 'r')
        params = {
            "reportId": self.report.id,
            "message": "Hello baby",
            "file": send_file,
        }
        content = encode_multipart('BoUnDaRyStRiNg', params)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

        response = self.client.post(reverse('reportcomment-list'), content, content_type=content_type)
        send_file.closed
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello baby')
        self.assertEqual(response_json['fileUrl'], 'hello.world.jpg')

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')
        self.assertEqual(comment.file_url, 'hello.world.jpg')
        self.assertEqual(comment.created_by, self.krystal)

    '''
    @patch('reports.api.upload_to_s3', mock_upload_to_s3)
    def test_post_api_report_comment_by_report_with_large_file(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        m = mock_open()
        with patch('__main__.open', m, create=True):
            send_file = open('/tmp/hello_large.world', 'r')
        params = {
            "message": "Hello baby",
            "file": send_file,
        }
        content = encode_multipart('BoUnDaRyStRiNg', params)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

        response = self.client.post(reverse('report-comment', args=[self.report.id]), content, content_type=content_type)
        self.assertEqual(response.status_code, 400)

    @patch('reports.api.upload_to_s3', mock_upload_to_s3)
    def test_post_api_report_comment_by_report_comment_with_large_file(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        m = mock_open()
        with patch('__main__.open', m, create=True):
            send_file = open('/tmp/hello_large.world', 'r')
        params = {
            "reportId": self.report.id,
            "message": "Hello baby",
            "file": send_file,
        }
        content = encode_multipart('BoUnDaRyStRiNg', params)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

        response = self.client.post(reverse('reportcomment-list'), content, content_type=content_type)
        self.assertEqual(response.status_code, 400)
    '''

    def test_post_api_report_comment_wih_user_cannot_access_by_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        params = {
            "message": "Hello baby",
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 403)

    def test_post_api_report_comment_wih_user_cannot_access_by_report_comment(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello baby",
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 403)
    '''
    def test_post_api_report_comment_on_area_that_child_of_permitted_administration_area_by_report(self):
        area = self.area.add_child(name='Namsan', location=self.area.location)
        report = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "message": "I am Back",
        }
        response = self.client.post(reverse('report-comment', args=[report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], report.id)
        self.assertEqual(response_json['message'], 'I am Back')

    def test_post_api_report_comment_on_area_that_child_of_permitted_administration_area_by_report_with_authority(self):
        area = self.area.add_child(name='Namsan', location=self.area.location)
        report = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "message": "I am Back",
        }
        response = self.client.post(reverse('report-comment', args=[report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], report.id)
        self.assertEqual(response_json['message'], 'I am Back')

    def test_post_api_report_comment_on_area_that_child_of_permitted_administration_area_by_report_comment(self):
        area = self.area.add_child(name='Namsan', location=self.area.location)
        report = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "message": "I am Back",
            "reportId": report.id,
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], report.id)
        self.assertEqual(response_json['message'], 'I am Back')

    def test_post_api_report_comment_on_area_that_child_of_permitted_administration_area_by_report_comment_with_authority(self):
        area = self.area.add_child(name='Namsan', location=self.area.location)
        report = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "message": "I am Back",
            "reportId": report.id,
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], report.id)
        self.assertEqual(response_json['message'], 'I am Back')
    '''
    def test_post_api_report_mention_comment_by_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "message": "Hello @[%s]" % self.jessica.username,
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s]' % self.jessica.username)
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention = Mention.objects.latest('id')
        self.assertEqual(mention.comment.id, comment.id)
        self.assertEqual(mention.mentioner, self.taeyeon)
        self.assertEqual(mention.mentionee, self.jessica)
        self.assertEqual(mention.is_notified, False)

    def test_post_api_report_mention_comment_by_report_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "message": "Hello @[%s]" % self.jessica.username,
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s]' % self.jessica.username)
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention = Mention.objects.latest('id')
        self.assertEqual(mention.comment.id, comment.id)
        self.assertEqual(mention.mentioner, self.krystal)
        self.assertEqual(mention.mentionee, self.jessica)
        self.assertEqual(mention.is_notified, False)

    def test_post_api_report_mentions_comment_by_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "message": "Hello @[%s] @[%s]" % (self.jessica.username, self.yoona.username)
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s] @[%s]' % (self.jessica.username, self.yoona.username))
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention1 = Mention.objects.filter(mentionee__id=self.jessica.id).latest('id')
        self.assertEqual(mention1.comment.id, comment.id)
        self.assertEqual(mention1.mentioner, self.taeyeon)
        self.assertEqual(mention1.mentionee, self.jessica)
        self.assertEqual(mention1.is_notified, False)

        mention2 = Mention.objects.filter(mentionee__id=self.yoona.id).latest('id')
        self.assertEqual(mention2.comment.id, comment.id)
        self.assertEqual(mention2.mentioner, self.taeyeon)
        self.assertEqual(mention2.mentionee, self.yoona)
        self.assertEqual(mention2.is_notified, False)

    def test_post_api_report_mentions_comment_by_report_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "message": "Hello @[%s] @[%s]" % (self.jessica.username, self.yoona.username)
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s] @[%s]' % (self.jessica.username, self.yoona.username))
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention1 = Mention.objects.filter(mentionee__id=self.jessica.id).latest('id')
        self.assertEqual(mention1.comment.id, comment.id)
        self.assertEqual(mention1.mentioner, self.krystal)
        self.assertEqual(mention1.mentionee, self.jessica)
        self.assertEqual(mention1.is_notified, False)

        mention2 = Mention.objects.filter(mentionee__id=self.yoona.id).latest('id')
        self.assertEqual(mention2.comment.id, comment.id)
        self.assertEqual(mention2.mentioner, self.krystal)
        self.assertEqual(mention2.mentionee, self.yoona)
        self.assertEqual(mention2.is_notified, False)

    def test_post_api_report_myself_mentions_comment_by_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "message": "Hello @[%s]" % self.taeyeon.username
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s]' % self.taeyeon.username)
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention = Mention.objects.latest('id')
        self.assertEqual(mention.comment.id, comment.id)
        self.assertEqual(mention.mentioner, self.taeyeon)
        self.assertEqual(mention.mentionee, self.taeyeon)
        self.assertEqual(mention.is_notified, True)

    def test_post_api_report_myself_mentions_comment_by_report_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "message": "Hello @[%s]" % self.krystal.username
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s]' % self.krystal.username)
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention = Mention.objects.latest('id')
        self.assertEqual(mention.comment.id, comment.id)
        self.assertEqual(mention.mentioner, self.krystal)
        self.assertEqual(mention.mentionee, self.krystal)
        self.assertEqual(mention.is_notified, True)

    def test_post_api_report_mention_comment_by_report_comment(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello @[%s]" % self.jessica.username,
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s]' % self.jessica.username)
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention = Mention.objects.latest('id')
        self.assertEqual(mention.comment.id, comment.id)
        self.assertEqual(mention.mentioner, self.taeyeon)
        self.assertEqual(mention.mentionee, self.jessica)
        self.assertEqual(mention.is_notified, False)

    def test_post_api_report_mention_comment_by_report_comment_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello @[%s]" % self.jessica.username,
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s]' % self.jessica.username)
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention = Mention.objects.latest('id')
        self.assertEqual(mention.comment.id, comment.id)
        self.assertEqual(mention.mentioner, self.krystal)
        self.assertEqual(mention.mentionee, self.jessica)
        self.assertEqual(mention.is_notified, False)

    def test_post_api_report_mentions_comment_by_report_comment(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello @[%s] @[%s]" % (self.jessica.username, self.yoona.username)
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s] @[%s]' % (self.jessica.username, self.yoona.username))
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention1 = Mention.objects.filter(mentionee__id=self.jessica.id).latest('id')
        self.assertEqual(mention1.comment.id, comment.id)
        self.assertEqual(mention1.mentioner, self.taeyeon)
        self.assertEqual(mention1.mentionee, self.jessica)
        self.assertEqual(mention1.is_notified, False)

        mention2 = Mention.objects.filter(mentionee__id=self.yoona.id).latest('id')
        self.assertEqual(mention2.comment.id, comment.id)
        self.assertEqual(mention2.mentioner, self.taeyeon)
        self.assertEqual(mention2.mentionee, self.yoona)
        self.assertEqual(mention2.is_notified, False)

    def test_post_api_report_mentions_comment_by_report_comment_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello @[%s] @[%s]" % (self.jessica.username, self.yoona.username)
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s] @[%s]' % (self.jessica.username, self.yoona.username))
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention1 = Mention.objects.filter(mentionee__id=self.jessica.id).latest('id')
        self.assertEqual(mention1.comment.id, comment.id)
        self.assertEqual(mention1.mentioner, self.krystal)
        self.assertEqual(mention1.mentionee, self.jessica)
        self.assertEqual(mention1.is_notified, False)

        mention2 = Mention.objects.filter(mentionee__id=self.yoona.id).latest('id')
        self.assertEqual(mention2.comment.id, comment.id)
        self.assertEqual(mention2.mentioner, self.krystal)
        self.assertEqual(mention2.mentionee, self.yoona)
        self.assertEqual(mention2.is_notified, False)

    def test_post_api_report_myself_mentions_comment_by_report_comment(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello @[%s]" % self.taeyeon.username
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s]' % self.taeyeon.username)
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention = Mention.objects.latest('id')
        self.assertEqual(mention.comment.id, comment.id)
        self.assertEqual(mention.mentioner, self.taeyeon)
        self.assertEqual(mention.mentionee, self.taeyeon)
        self.assertEqual(mention.is_notified, True)

    def test_post_api_report_myself_mentions_comment_by_report_comment_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello @[%s]" % self.krystal.username
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['message'], 'Hello @[%s]' % self.krystal.username)
        self.assertEqual(response_json['fileUrl'], None)

        comment = ReportComment.objects.latest('id')

        mention = Mention.objects.latest('id')
        self.assertEqual(mention.comment.id, comment.id)
        self.assertEqual(mention.mentioner, self.krystal)
        self.assertEqual(mention.mentionee, self.krystal)
        self.assertEqual(mention.is_notified, True)

    def test_get_api_report_comment_by_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "message": "Hello baby",
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')

        response = self.client.get(reverse('report-comments', args=[self.report.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        comment1 = response_json[0]
        self.assertEqual(comment1['reportId'], self.report.id)
        self.assertEqual(comment1['message'], u'@[%(username)s] ได้ทำการตั้งค่าสถานะเป็น %(state)s' % 
            {'username': self.report.created_by.username, 'state': 'Report'})

        comment2 = response_json[1]
        self.assertEqual(comment2['reportId'], self.report.id)
        self.assertEqual(comment2['message'], 'Hello baby')

    def test_get_api_report_comment_by_report_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "message": "Hello baby",
        }
        response = self.client.post(reverse('report-comment', args=[self.report.id]), params)
        self.assertEqual(response.status_code, 201)

        comment = ReportComment.objects.latest('id')
        self.assertEqual(comment.report, self.report)
        self.assertEqual(comment.message, 'Hello baby')

        response = self.client.get(reverse('report-comments', args=[self.report.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        comment1 = response_json[0]
        self.assertEqual(comment1['reportId'], self.report.id)
        self.assertEqual(comment1['message'], u'@[%(username)s] ได้ทำการตั้งค่าสถานะเป็น %(state)s' % 
            {'username': self.report.created_by.username, 'state': 'Report'})

        comment2 = response_json[1]
        self.assertEqual(comment2['reportId'], self.report.id)
        self.assertEqual(comment2['message'], 'Hello baby')
    '''
    def test_get_api_report_comment_that_area_is_child_of_permitted_administration_area_by_report_comment(self):
        area = self.area.add_child(name='Namsan', location=self.area.location)
        report = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=area)
        comment = factory.create_report_comment(report=report)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reportcomment-detail', args=[comment.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], comment.report.id)
        self.assertEqual(response_json['message'], comment.message)

    def test_get_api_report_comment_that_area_is_child_of_permitted_administration_area_by_report_comment_with_authority(self):
        area = self.area.add_child(name='Namsan', location=self.area.location)
        report = factory.create_report(created_by=self.krystal, type=self.type,
            administration_area=area)
        comment = factory.create_report_comment(report=report)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('reportcomment-detail', args=[comment.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], comment.report.id)
        self.assertEqual(response_json['message'], comment.message)
    '''
    def test_get_api_report_comment_wih_user_cannot_access_by_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('report-comments', args=[self.report.id]))
        self.assertEqual(response.status_code, 403)


class TestApiAdministrationAreaList(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user()
        self.minah = factory.create_user(is_superuser=True, is_staff=True)
        self.krystal = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.krystal)

        self.authority_1 = factory.create_authority()
        self.authority_1.users.add(self.jessica)

        self.area1 = factory.create_administration_area(name='Seoul', authority=self.authority_1)
        self.area2 = factory.create_administration_area(name='Tokyo', authority=self.authority)
        self.area2_1 = self.area2.add_child(name='Namsan', location=self.area2.location)
        self.area2_1_1 = self.area2_1.add_child(name='Namsan Tower', location=self.area2.location)
        self.area3 = factory.create_administration_area(name='Chiang Mai', authority=self.authority)

        self.authority_1.inherits.add(self.authority)

    def test_api_list_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('administrationarea-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

        area1 = response_json[0]
        self.assertEqual(area1['id'], self.area3.id)
        self.assertEqual(area1['name'], self.area3.name)
        self.assertEqual(area1['address'], self.area3.address)
        # self.assertEqual(area1['parentName'], '')
        # self.assertEqual(area1['isLeaf'], True)

        # area2 = response_json[1]
        # self.assertEqual(area2['id'], self.area2_1.id)
        # self.assertEqual(area2['name'], self.area2_1.name)
        # self.assertEqual(area2['address'], self.area2_1.address)
        # # self.assertEqual(area2['parentName'], self.area2.name)
        # # self.assertEqual(area2['isLeaf'], False)
        #
        # area3 = response_json[2]
        # self.assertEqual(area3['id'], self.area2_1_1.id)
        # self.assertEqual(area3['name'], self.area2_1_1.name)
        # self.assertEqual(area3['address'], self.area2_1_1.address)
        # # self.assertEqual(area3['parentName'], self.area2_1.name)
        # # self.assertEqual(area3['isLeaf'], True)

        area4 = response_json[1]
        self.assertEqual(area4['id'], self.area1.id)
        self.assertEqual(area4['name'], self.area1.name)
        self.assertEqual(area4['address'], self.area1.address)
        # self.assertEqual(area4['parentName'], '')
        # self.assertEqual(area4['isLeaf'], True)

        area5 = response_json[2]
        self.assertEqual(area5['id'], self.area2.id)
        self.assertEqual(area5['name'], self.area2.name)
        self.assertEqual(area5['address'], self.area2.address)
        # self.assertEqual(area5['parentName'], '')
        # self.assertEqual(area5['isLeaf'], False)

    def test_api_list_administration_area_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('administrationarea-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

    def test_api_list_administration_area_only_has_permission_on_those_administration_areas(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('administrationarea-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        area1 = response_json[0]
        self.assertEqual(area1['id'], self.area1.id)
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['address'], self.area1.address)
        # self.assertEqual(area1['parentName'], '')

    def test_api_list_administration_area_only_group_has_role_reporter(self):
        group_a = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)
        area = factory.create_administration_area()
        factory.create_group_administration_area(group=group_a, administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('administrationarea-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

    def test_api_list_administration_area_return_empty_list_if_not_have_any_permission(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('administrationarea-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 0)

    def test_staff_can_get_all_api_list_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.minah.auth_token.key)
        response = self.client.get(reverse('administrationarea-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 5)

    def test_anonymous_cannot_access_api_list_administration_area(self):
        response = self.client.get(reverse('administrationarea-list'))
        self.assertEqual(response.status_code, 401)


class TestApiAdministrationArea(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user(is_staff=True, is_superuser=True)
        self.krystal = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.krystal)

        self.area1 = factory.create_administration_area(authority=self.authority)
        self.area2 = factory.create_administration_area(authority=self.authority)

    def test_api_get_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('administrationarea-detail', args=[self.area1.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], self.area1.id)
        self.assertEqual(response_json['name'], self.area1.name)
        self.assertEqual(response_json['address'], self.area1.address)

    def test_api_get_administration_area_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('administrationarea-detail', args=[self.area1.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], self.area1.id)
        self.assertEqual(response_json['name'], self.area1.name)
        self.assertEqual(response_json['address'], self.area1.address)

    '''
    def test_api_get_administration_area_that_is_child_of_area_that_has_permission(self):
        area = self.area1.add_child(name='Namsan', location=self.area1.location)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('administrationarea-detail', args=[area.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], area.id)
        self.assertEqual(response_json['name'], area.name)
        self.assertEqual(response_json['address'], area.address)

    def test_api_get_administration_area_that_is_child_of_area_that_has_permission_with_authority(self):
        area = self.area1.add_child(name='Namsan', location=self.area1.location)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('administrationarea-detail', args=[area.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['id'], area.id)
        self.assertEqual(response_json['name'], area.name)
        self.assertEqual(response_json['address'], area.address)
    '''
    def test_cannot_get_api_get_administration_area_if_user_dont_have_authorized(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('administrationarea-detail', args=[self.area1.id]))
        self.assertEqual(response.status_code, 403)

    def test_cannot_get_api_get_administration_area_if_group_is_not_has_role_reporter(self):
        group_a = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)
        area = factory.create_administration_area()
        factory.create_group_administration_area(group=group_a, administration_area=area)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('administrationarea-detail', args=[area.id]))
        self.assertEqual(response.status_code, 403)

    def test_cannot_get_api_get_administration_area_if_not_exists(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('administrationarea-detail', args=[self.area1.id+100]))
        self.assertEqual(response.status_code, 404)

    def test_staff_can_get_api_get_administration_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('administrationarea-detail', args=[self.area1.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_cannot_access_api_get_administration_area(self):
        response = self.client.get(reverse('administrationarea-detail', args=[self.area1.id]))
        self.assertEqual(response.status_code, 401)


class TestApiDashboard(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)
        call_command('clear_graph', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user(is_staff=True)
        self.krystal = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.krystal)

        self.authority_1 = factory.create_authority()
        self.authority_1.users.add(self.jessica)

        self.type = factory.create_report_type(authority=self.authority)
        self.area1 = factory.create_administration_area(authority=self.authority)
        self.area2 = factory.create_administration_area(authority=self.authority_1)

        self.authority_1.inherits.add(self.authority)

        self.report1 = factory.create_report(type=self.type, administration_area=self.area1, negative=True)
        self.report2 = factory.create_report(type=self.type, administration_area=self.area1, negative=False)
        self.report3 = factory.create_report(type=self.type, administration_area=self.area2, negative=True)

    def test_get_api_dashboard_with_staff_user(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        response = self.client.get(reverse('dashboard_villages'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)
        response_json = order_list_by_id(response_json)

        area1 = response_json[0]
        self.assertEqual(area1['id'], self.area1.id)
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['positive'], 1)
        self.assertEqual(area1['negative'], 1)

        area2 = response_json[1
        ]
        self.assertEqual(area2['id'], self.area2.id)
        self.assertEqual(area2['name'], self.area2.name)
        self.assertEqual(area2['positive'], 0)
        self.assertEqual(area2['negative'], 1)

    def test_get_api_dashboard_with_full_access_user(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('dashboard_villages'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        area1 = response_json[0]
        self.assertEqual(area1['id'], self.area1.id)
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['positive'], 1)
        self.assertEqual(area1['negative'], 1)

        area2 = response_json[1]
        self.assertEqual(area2['id'], self.area2.id)
        self.assertEqual(area2['name'], self.area2.name)
        self.assertEqual(area2['positive'], 0)
        self.assertEqual(area2['negative'], 1)

    def test_get_api_dashboard_with_full_access_user_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('dashboard_villages'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        area1 = response_json[0]
        self.assertEqual(area1['id'], self.area2.id)
        self.assertEqual(area1['name'], self.area2.name)
        self.assertEqual(area1['positive'], 0)
        self.assertEqual(area1['negative'], 1)

    def test_get_api_dashboard_with_some_access_user(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('dashboard_villages'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        area1 = response_json[0]
        self.assertEqual(area1['id'], self.area2.id)
        self.assertEqual(area1['name'], self.area2.name)
        self.assertEqual(area1['positive'], 0)
        self.assertEqual(area1['negative'], 1)
    '''
    def test_get_api_dashboard_always_include_report_type_0(self):
        try:
            default_positive_type = ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            default_positive_type = ReportType.objects.create(id=0, code='positive-report', name='positive report')

        factory.create_report(type=default_positive_type, administration_area=self.area1, negative=False)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('dashboard_villages'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        area1 = response_json[0]
        self.assertEqual(area1['id'], self.area1.id)
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['address'], self.area1.address)
        self.assertEqual(area1['positive'], 2)
        self.assertEqual(area1['negative'], 1)

        area2 = response_json[1]
        self.assertEqual(area2['id'], self.area2.id)
        self.assertEqual(area2['name'], self.area2.name)
        self.assertEqual(area2['address'], self.area2.address)
        self.assertEqual(area2['positive'], 0)
        self.assertEqual(area2['negative'], 1)

    def test_get_api_dashboard_always_include_report_type_0_with_authority(self):
        try:
            default_positive_type = ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            default_positive_type = ReportType.objects.create(id=0, code='positive-report', name='positive report')
        factory.create_report(type=default_positive_type, administration_area=self.area1, negative=False)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('dashboard_villages'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        area1 = response_json[0]
        self.assertEqual(area1['id'], self.area1.id)
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['address'], self.area1.address)
        self.assertEqual(area1['positive'], 2)
        self.assertEqual(area1['negative'], 1)
    '''
'''
@patch('django_redis.get_redis_connection', mock_strict_redis_client)
class TestApiReportSummaryByMonth(APITestCase):
    def setUp(self):

        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user(username='taeyeon')
        self.jessica = factory.create_user(username='jessica')
        self.yoona = factory.create_user(username='yoona')

        self.authority = factory.create_authority()
        self.authority.users.add(self.yoona)

        self.group_a = factory.add_user_to_new_group_type_administration_area(user=self.taeyeon)
        self.group_r = factory.add_user_to_new_group_type_report_type(user=self.taeyeon)

        self.type1 = factory.create_report_type()
        self.type2 = factory.create_report_type()
        self.type3 = factory.create_report_type()
        factory.create_group_report_type(group=self.group_r, report_type=self.type1)
        factory.create_group_report_type(group=self.group_r, report_type=self.type2)
        self.authority.report_types.add(self.type1)
        self.authority.report_types.add(self.type2)

        self.area1 = factory.create_administration_area()
        self.area2 = factory.create_administration_area()
        self.area3 = factory.create_administration_area()
        factory.create_group_administration_area(group=self.group_a, administration_area=self.area1)
        factory.create_group_administration_area(group=self.group_a, administration_area=self.area2)
        self.authority.administration_areas.add(self.area1)
        self.authority.administration_areas.add(self.area2)

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type2,
            administration_area=self.area2, incident_date=datetime.date(2014, 11, 14), negative=True)
        self.report2 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area1, incident_date=datetime.date(2014, 11, 14), negative=False)
        self.report3 = factory.create_report(created_by=self.jessica, type=self.type1,
            administration_area=self.area2, incident_date=datetime.date(2014, 11, 27), negative=True)
        self.report4 = factory.create_report(created_by=self.taeyeon, type=self.type3,
            administration_area=self.area2, incident_date=datetime.date(2014, 11, 14), negative=True)
        self.report5 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area3, incident_date=datetime.date(2014, 11, 3), negative=False)

    def test_api_report_summary_by_month(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        params = {'month': '11/2014'}
        response = self.client.get(reverse('reports_summary_by_month'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

        user1 = response_json[0]
        self.assertEqual(user1['fullname'], self.jessica.get_full_name())
        self.assertEqual(user1['dates'][26]['date'], '27-11-2014')
        self.assertEqual(user1['dates'][26]['positive'], 0)
        self.assertEqual(user1['dates'][26]['negative'], 1)
        self.assertEqual(user1['dates'][26]['total'], 1)

        user2 = response_json[1]
        self.assertEqual(user2['fullname'], self.taeyeon.get_full_name())
        self.assertEqual(user2['dates'][2]['date'], '03-11-2014')
        self.assertEqual(user2['dates'][2]['positive'], 1)
        self.assertEqual(user2['dates'][2]['negative'], 0)
        self.assertEqual(user2['dates'][2]['total'], 1)
        self.assertEqual(user2['dates'][13]['date'], '14-11-2014')
        self.assertEqual(user2['dates'][13]['positive'], 1)
        self.assertEqual(user2['dates'][13]['negative'], 2)
        self.assertEqual(user2['dates'][13]['total'], 3)

        user3 = response_json[2]
        self.assertEqual(user3['fullname'], self.yoona.get_full_name())

    def test_api_report_summary_by_month_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)

        params = {'month': '11/2014'}
        response = self.client.get(reverse('reports_summary_by_month'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

        user1 = response_json[0]
        self.assertEqual(user1['fullname'], self.jessica.get_full_name())
        self.assertEqual(user1['dates'][26]['date'], '27-11-2014')
        self.assertEqual(user1['dates'][26]['positive'], 0)
        self.assertEqual(user1['dates'][26]['negative'], 1)
        self.assertEqual(user1['dates'][26]['total'], 1)

        user2 = response_json[1]
        self.assertEqual(user2['fullname'], self.taeyeon.get_full_name())
        self.assertEqual(user2['dates'][2]['date'], '03-11-2014')
        self.assertEqual(user2['dates'][2]['positive'], 1)
        self.assertEqual(user2['dates'][2]['negative'], 0)
        self.assertEqual(user2['dates'][2]['total'], 1)
        self.assertEqual(user2['dates'][13]['date'], '14-11-2014')
        self.assertEqual(user2['dates'][13]['positive'], 1)
        self.assertEqual(user2['dates'][13]['negative'], 2)
        self.assertEqual(user2['dates'][13]['total'], 3)

        user3 = response_json[2]
        self.assertEqual(user3['fullname'], self.yoona.get_full_name())

    def test_api_report_summary_by_month_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('reports_summary_by_month'))
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['month'], 'Invalid month. Please try again. (eg. 3/2014)')

    def test_anonymous_cannot_access_api_report_summary_by_month(self):
        response = self.client.get(reverse('reports_summary_by_month'))
        self.assertEqual(response.status_code, 401)
'''

class TestApiSupport(APITestCase):

    def setUp(self):
        common_public_setup(self)

    def test_action(self):

        user1 = factory.create_user(display_password='password', status=USER_STATUS_ADDITION_VOLUNTEER, is_anonymous=False,
                                    is_public=True)
        user2 = factory.create_user(display_password='password', status=USER_STATUS_ADDITION_VOLUNTEER, is_anonymous=False,
                                    is_public=True)

        report1 = factory.create_report(type=self.report_type, created_by=self.user)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + user1.auth_token.key)
        params = {
            'reportGuid': report1.guid,
            'message': 'Hello World 1',
            'isLike': True,
            'isMeToo': True
        }
        response = self.client.post(reverse('report_add_support'), params)

        notifications = Notification.objects.filter(created_by=user1, receive_user=self.user).order_by('-id')
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications[0].type, SUPPORT_LIKE_ME_TOO_COMMENT)

        params = {
            'reportGuid': report1.guid,
            'message': ' ',
            'isLike': True,
            'isMeToo': True
        }
        response = self.client.post(reverse('report_add_support'), params)
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications[0].type, SUPPORT_LIKE_ME_TOO_COMMENT)

        params = {
            'reportGuid': report1.guid,
            'message': 'Hello World 2',
            'isLike': True,
            'isMeToo': True
        }
        response = self.client.post(reverse('report_add_support'), params)
        self.assertEqual(notifications.count(), 2)
        self.assertEqual(notifications[0].type, SUPPORT_COMMENT)

        params = {
            'reportGuid': report1.guid,
            'message': '',
            'isLike': False,
            'isMeToo': False
        }
        response = self.client.post(reverse('report_add_support'), params)
        self.assertEqual(notifications.count(), 2)
        self.assertEqual(notifications[0].type, SUPPORT_COMMENT)

        params = {
            'reportGuid': report1.guid,
            'message': '',
            'isLike': True,
            'isMeToo': True
        }
        response = self.client.post(reverse('report_add_support'), params)
        self.assertEqual(notifications.count(), 2)
        self.assertEqual(notifications[0].type, SUPPORT_COMMENT)


        report2 = factory.create_report(type=self.report_type, created_by=self.user)

        params = {
            'reportGuid': report2.guid,
            'message': '',
            'isLike': True,
            'isMeToo': False
        }
        response = self.client.post(reverse('report_add_support'), params)

        notifications = Notification.objects.filter(created_by=user1, receive_user=self.user).order_by('-id')
        self.assertEqual(notifications.count(), 3)
        self.assertEqual(notifications[0].type, SUPPORT_LIKE)


        report3 = factory.create_report(type=self.report_type, created_by=self.user)

        params = {
            'reportGuid': report3.guid,
            'message': '',
            'isLike': False,
            'isMeToo': True
        }
        response = self.client.post(reverse('report_add_support'), params)

        notifications = Notification.objects.filter(created_by=user1, receive_user=self.user).order_by('-id')
        self.assertEqual(notifications.count(), 4)
        self.assertEqual(notifications[0].type, SUPPORT_ME_TOO)


        report4 = factory.create_report(type=self.report_type, created_by=self.user)

        params = {
            'reportGuid': report4.guid,
            'message': '',
            'isLike': True,
            'isMeToo': True
        }
        response = self.client.post(reverse('report_add_support'), params)

        notifications = Notification.objects.filter(created_by=user1, receive_user=self.user).order_by('-id')
        self.assertEqual(notifications.count(), 5)
        self.assertEqual(notifications[0].type, SUPPORT_LIKE_ME_TOO)


class TestApiReportReportAbuse(APITestCase):
    def setUp(self):
        try:
            ReportType.objects.get(id=0)
        except ReportType.DoesNotExist:
            ReportType.objects.create(
                id=0,
                name='Positive Report Type',
                form_definition='{}',
                version=0,
            )

        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user()
        self.krystal = factory.create_user(is_anonymous=True)

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.jessica)
        self.authority.users.add(self.yoona)
        self.authority.users.add(self.krystal)

        self.type = factory.create_report_type(authority=self.authority)
        self.area = factory.create_administration_area(authority=self.authority)

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type,
            administration_area=self.area)

        self.report2 = factory.create_report(created_by=self.jessica, type=self.type,
            administration_area=self.area)

    def test_post_create_report_report_abuse(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reason": "No reason",
        }
        response = self.client.post(reverse('report-reportAbuse', args=[self.report2.id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report2.id)
        self.assertEqual(response_json['reason'], 'No reason')

        report_abuse = ReportAbuse.objects.latest('id')
        self.assertEqual(report_abuse.report, self.report2)
        self.assertEqual(report_abuse.reason, 'No reason')
        self.assertEqual(report_abuse.created_by, self.taeyeon)

    def test_post_create_report_report_abuse_with_multi_users(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        params = {
            "reason": "No reason, It's me",
        }
        response = self.client.post(reverse('report-reportAbuse', args=[self.report1.id]), params)
        self.assertEqual(response.status_code, 201)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reason": "No reason, :P",
        }

        response = self.client.post(reverse('report-reportAbuse', args=[self.report1.id]), params)
        self.assertEqual(response.status_code, 201)

        response = self.client.get(reverse('report-reportAbuses', args=[self.report1.id]))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        # user1 = response_json[0]
        # self.assertEqual(user1['id'], self.jessica.id)
        # self.assertEqual(user1['firstName'], self.jessica.first_name)
        #
        # user2 = response_json[1]
        # self.assertEqual(user2['id'], self.yoona.id)
        # self.assertEqual(user2['firstName'], self.yoona.first_name)

    def test_post_create_report_report_abuse_without_reason(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.post(reverse('report-reportAbuse', args=[self.report2.id]))
        self.assertEqual(response.status_code, 400)

    def test_post_api_report_report_abuse_wih_anonymous_by_report(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reason": "No reason, :P",
        }
        response = self.client.post(reverse('report-reportAbuse', args=[self.report1.id]), params)
        self.assertEqual(response.status_code, 400)

    def test_post_api_report_report_abuse_no_token(self):
        params = {
            "reason": "No reason, :P",
        }
        response = self.client.post(reverse('report-reportAbuse', args=[self.report1.id]), params)
        self.assertEqual(response.status_code, 401)


