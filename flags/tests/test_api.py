# -*- encoding: utf-8 -*-
import json

from django.core.management import call_command
from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase

from common import factory
from common.constants import (PRIORITY_CASE, PRIORITY_CHOICES, GROUP_WORKING_TYPE_REPORT_TYPE,
    GROUP_WORKING_TYPE_ADMINSTRATION_AREA, GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA,
    GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE, GROUP_ROLE_PROSPECTOR)
from flags.models import Flag
from logs.models import LogAction
from reports.models import ReportComment, Report


class TestApiFlagList(APITestCase):
    def setUp(self):
        call_command('log_action_create', interactive=False, verbosity=0)
        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.yoona)

        self.group_a = factory.add_user_to_new_group_type_administration_area(user=self.taeyeon)
        self.group_r = factory.add_user_to_new_group_type_report_type(user=self.taeyeon)

        self.type = factory.create_report_type()
        self.area = factory.create_administration_area()

        self.authority.report_types.add(self.type)
        self.authority.administration_areas.add(self.area)

        self.report = factory.create_report(created_by=self.taeyeon, type=self.type,
                                            administration_area=self.area, form_data={
                "symptom": "cough,headache,pain",
                "sickCount": 4,
            })

        self.group_report_type = factory.create_group_report_type(group=self.group_r, report_type=self.type)
        self.group_administration_area = factory.create_group_administration_area(group=self.group_a, administration_area=self.area)

        self.flag = factory.create_flag(report=self.report, priority=1, flag_owner=self.taeyeon)

        factory.create_configuration(system='web.template.report', key='comment_flag', value='@[%(username)s] set report priority to %(flag)s')

    def test_get_api_flag_list(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = { "reportId": self.report.id, }
        response = self.client.get(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 200)

    def test_get_api_lastest_flag_list(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "page_size": 1,
        }
        response = self.client.get(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        flag = response_json[0]
        self.assertEqual(flag['reportId'], self.report.id)
        self.assertEqual(flag['priority'], 1)
        self.assertEqual(flag['flagOwner'], self.taeyeon.username)

    def test_get_api_lastest_flag_list_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reportId": self.report.id,
            "page_size": 1,
        }
        response = self.client.get(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        flag = response_json[0]
        self.assertEqual(flag['reportId'], self.report.id)
        self.assertEqual(flag['priority'], 1)
        self.assertEqual(flag['flagOwner'], self.taeyeon.username)

    def test_get_api_flag_detail_with_user_can_access(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('flag-detail', args=[self.flag.id]))
        self.assertEqual(response.status_code, 200)

    def test_get_api_flag_detail_with_user_can_not_access(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('flag-detail', args=[self.flag.id]))
        self.assertEqual(response.status_code, 403)

    def test_post_api_flag_list(self):
        comment = ReportComment.objects.filter(report=self.report.id).delete()
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "priority": 1,
        }

        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 1)
        self.assertEqual(response_json['flagOwner'], self.taeyeon.username)

        params = {
            "reportId": self.report.id,
            "priority": 2,
        }

        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 2)
        self.assertEqual(response_json['flagOwner'], self.taeyeon.username)

        params = {
            "reportId": self.report.id,
        }
        response = self.client.get(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)

        comment1 = response_json[0]
        self.assertEqual(comment1['reportId'], self.report.id)
        self.assertEqual(comment1['message'], '@[%s] set report priority to %s' % (self.taeyeon.username, PRIORITY_CHOICES[0][1]))
        self.assertEqual(comment1['fileUrl'], None)

        comment2 = response_json[1]
        self.assertEqual(comment2['reportId'], self.report.id)
        self.assertEqual(comment2['message'], '@[%s] set report priority to %s' % (self.taeyeon.username, PRIORITY_CHOICES[1][1]))
        self.assertEqual(comment2['fileUrl'], None)

    def test_post_api_flag_list_with_authority(self):
        comment = ReportComment.objects.filter(report=self.report.id).delete()
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reportId": self.report.id,
            "priority": 1,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 1)
        self.assertEqual(response_json['flagOwner'], self.yoona.username)

        params = {
            "reportId": self.report.id,
            "priority": 2,
        }

        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 2)
        self.assertEqual(response_json['flagOwner'], self.yoona.username)

        params = {
            "reportId": self.report.id,
        }
        response = self.client.get(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)

        comment1 = response_json[0]
        self.assertEqual(comment1['reportId'], self.report.id)
        self.assertEqual(comment1['message'], '@[%s] set report priority to %s' % (self.yoona.username, PRIORITY_CHOICES[0][1]))
        self.assertEqual(comment1['fileUrl'], None)

        comment2 = response_json[1]
        self.assertEqual(comment2['reportId'], self.report.id)
        self.assertEqual(comment2['message'], '@[%s] set report priority to %s' % (self.yoona.username, PRIORITY_CHOICES[1][1]))
        self.assertEqual(comment2['fileUrl'], None)

    def test_post_api_flag_priority_1_will_set_that_report_to_be_not_negative(self):
        comment = ReportComment.objects.filter(report=self.report.id).delete()
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "priority": 1,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 1)
        self.assertEqual(response_json['flagOwner'], self.taeyeon.username)
        self.assertFalse(response_json['reportNegative'])

        report = Report.objects.get(id=self.report.id)
        self.assertFalse(report.negative)

        # SET AGAIN
        params = {
            "reportId": self.report.id,
            "priority": 2,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 2)
        self.assertEqual(response_json['flagOwner'], self.taeyeon.username)
        self.assertTrue(response_json['reportNegative'])

        report = Report.objects.get(id=self.report.id)
        self.assertEqual(report.priority, 2)
        self.assertTrue(report.negative)

    def test_post_api_flag_priority_1_will_set_that_report_to_be_not_negative_with_suthority(self):
        comment = ReportComment.objects.filter(report=self.report.id).delete()
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reportId": self.report.id,
            "priority": 1,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 1)
        self.assertEqual(response_json['flagOwner'], self.yoona.username)
        self.assertFalse(response_json['reportNegative'])

        report = Report.objects.get(id=self.report.id)
        self.assertFalse(report.negative)

        # SET AGAIN
        params = {
            "reportId": self.report.id,
            "priority": 2,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 2)
        self.assertEqual(response_json['flagOwner'], self.yoona.username)
        self.assertTrue(response_json['reportNegative'])

        report = Report.objects.get(id=self.report.id)
        self.assertEqual(report.priority, 2)
        self.assertTrue(report.negative)

    def test_post_api_flag_priority_CASE_will_check_permission_on_group(self):
        comment = ReportComment.objects.filter(report=self.report.id).delete()
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "priority": PRIORITY_CASE,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 403)

        group1 = factory.add_user_to_new_group(user=self.taeyeon,
                                               type=GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA)
        group2 = factory.add_user_to_new_group(user=self.taeyeon,
                                               type=GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE)

        factory.create_group_administration_area(group=group1, administration_area=self.area)
        factory.create_group_report_type(group=group2, report_type=self.type)

        # HAVE PERMISSION
        params = {
            "reportId": self.report.id,
            "priority": PRIORITY_CASE,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], PRIORITY_CASE)
        self.assertEqual(response_json['flagOwner'], self.taeyeon.username)
        self.assertTrue(response_json['reportNegative'])

        report = Report.objects.get(id=self.report.id)
        self.assertEqual(report.priority, PRIORITY_CASE)

    def test_post_api_flag_priority_CASE_will_check_permission_on_group_report_type_and_area(self):
        comment = ReportComment.objects.filter(report=self.report.id).delete()
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        group1 = factory.add_user_to_new_group(user=self.taeyeon,
                                               type=GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA)
        group2 = factory.add_user_to_new_group(user=self.taeyeon,
                                               type=GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE)

        factory.create_group_administration_area(group=group1)
        factory.create_group_report_type(group=group2)

        # HAVE PERMISSION
        params = {
            "reportId": self.report.id,
            "priority": PRIORITY_CASE,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 403)

    def test_post_api_flag_priority_CASE_will_check_permission_on_group_report_type_and_descendant_area(self):
        comment = ReportComment.objects.filter(report=self.report.id).delete()
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        group1 = factory.add_user_to_new_group(user=self.taeyeon,
                                               type=GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA)
        group2 = factory.add_user_to_new_group(user=self.taeyeon,
                                               type=GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE)

        area = self.area.add_child(name='Namsan', location=self.area.location)
        report = factory.create_report(created_by=self.taeyeon, type=self.type,
                                       administration_area=area, form_data={
                "symptom": "cough,headache,pain",
                "sickCount": 7,
            })

        factory.create_group_administration_area(group=group1, administration_area=self.area)
        factory.create_group_report_type(group=group2, report_type=self.type)

        # HAVE PERMISSION
        params = {
            "reportId": report.id,
            "priority": PRIORITY_CASE,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], report.id)
        self.assertEqual(response_json['priority'], PRIORITY_CASE)
        self.assertEqual(response_json['flagOwner'], self.taeyeon.username)
        self.assertTrue(response_json['reportNegative'])

        report = Report.objects.get(id=report.id)
        self.assertEqual(report.priority, PRIORITY_CASE)

    def test_post_api_flag_from_priority_case_to_others_will_set_that_report_parent_to_none(self):
        comment = ReportComment.objects.filter(report=self.report.id).delete()
        self.report.parent = factory.create_report()
        self.report.save()

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "priority": 2,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 2)
        self.assertEqual(response_json['flagOwner'], self.taeyeon.username)
        self.assertTrue(response_json['reportNegative'])

        report = Report.objects.get(id=self.report.id)
        self.assertEqual(report.priority, 2)
        self.assertFalse(report.parent)

    def test_post_api_flag_from_priority_case_to_others_will_set_that_report_parent_to_none_with_authority(self):
        comment = ReportComment.objects.filter(report=self.report.id).delete()
        self.report.parent = factory.create_report()
        self.report.save()

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reportId": self.report.id,
            "priority": 2,
        }
        response = self.client.post(reverse('flag-list'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['reportId'], self.report.id)
        self.assertEqual(response_json['priority'], 2)
        self.assertEqual(response_json['flagOwner'], self.yoona.username)
        self.assertTrue(response_json['reportNegative'])

        report = Report.objects.get(id=self.report.id)
        self.assertEqual(report.priority, 2)
        self.assertFalse(report.parent)