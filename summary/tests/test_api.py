# -*- encoding: utf-8 -*-

import datetime
import json
import urllib2

from django.core.management import call_command
from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase

from common import factory
from common.constants import (GROUP_WORKING_TYPE_REPORT_TYPE, 
    GROUP_WORKING_TYPE_ADMINSTRATION_AREA, USER_STATUS_VOLUNTEER)
from reports.models import Report


def order_list_by_id(tmp_list):
    _tmp_dict = {}
    for obj in tmp_list:
        _tmp_dict[obj['id']] = obj

    results = []
    for value in sorted(_tmp_dict.items()):
        results.append(value[1])
    return results


class TestApiSummaryByNumberOfReport(APITestCase):
    def setUp(self):
        call_command('clear_index', interactive=False, verbosity=0)
        
        self.taeyeon = factory.create_user(username='TaeYeon', status=USER_STATUS_VOLUNTEER)
        self.jessica = factory.create_user(username='Jessica', status=USER_STATUS_VOLUNTEER)
        self.yoona = factory.create_user(username='Yoona', is_staff=True)
        self.krystal = factory.create_user(username='Krytal')

        self.authority = factory.create_authority()
        self.authority.users.add(self.krystal)

        # authority [krystal][report_type: 1,2][area: 1,2,3]
        # authority_1 [taeyeon][report_type: 1,2][area: 1,2,3]
        # authority_2 [jessica][report_type: 1,2][area: 2]

        self.type1 = factory.create_report_type(authority=self.authority)
        self.type2 = factory.create_report_type(authority=self.authority)
        self.type3 = factory.create_report_type(authority=self.authority)

        self.authority_1 = factory.create_authority()
        self.authority_1.users.add(self.taeyeon)
        self.area1 = factory.create_administration_area(authority=self.authority_1)

        self.authority_2 = factory.create_authority()
        self.authority_2.users.add(self.jessica)
        self.area2 = factory.create_administration_area(authority=self.authority_2)

        self.area3 = factory.create_administration_area(authority=self.authority_1)

        self.authority_1.inherits.add(self.authority)
        self.authority_2.inherits.add(self.authority_1)

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type2,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 13), 
            date=datetime.datetime(2014, 9, 13, 0, 0, 0), negative=True)
        self.report2 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area1, incident_date=datetime.date(2014, 9, 13), 
            date=datetime.datetime(2014, 9, 13, 22, 0, 0), negative=False)
        self.report3 = factory.create_report(created_by=self.jessica, type=self.type1,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 11), 
            date=datetime.datetime(2014, 9, 11, 0, 0, 0), negative=True)
        self.report4 = factory.create_report(created_by=self.taeyeon, type=self.type3,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 12), 
            date=datetime.datetime(2014, 9, 12, 0, 0, 0), negative=True)
        self.report5 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area3, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 9, 0, 0, 0), negative=False)

    def test_api_summary_by_number_of_reports_with_staff(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014'}
        response = self.client.get(reverse('summary_by_number_of_report'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)
        response_json = order_list_by_id(response_json)

        area1 = response_json[0]
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['totalReport'], 1)
        self.assertEqual(area1['positiveReport'], 1)
        self.assertEqual(area1['negativeReport'], 0)
        self.assertEqual(area1['dates'][1]['date'], '09-09-2014')
        self.assertEqual(area1['dates'][1]['dayOfWeek'], 'Tuesday')
        self.assertEqual(area1['dates'][1]['positive'], 0)
        self.assertEqual(area1['dates'][1]['negative'], 0)
        self.assertEqual(area1['dates'][1]['total'], 0)
        self.assertEqual(area1['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area1['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area1['dates'][5]['positive'], 1)
        self.assertEqual(area1['dates'][5]['negative'], 0)
        self.assertEqual(area1['dates'][5]['total'], 1)

        area2 = response_json[1]
        self.assertEqual(area2['name'], self.area2.name)
        self.assertEqual(area2['totalReport'], 3)
        self.assertEqual(area2['positiveReport'], 0)
        self.assertEqual(area2['negativeReport'], 3)
        self.assertEqual(area2['dates'][3]['date'], '11-09-2014')
        self.assertEqual(area2['dates'][3]['dayOfWeek'], 'Thursday')
        self.assertEqual(area2['dates'][3]['positive'], 0)
        self.assertEqual(area2['dates'][3]['negative'], 1)
        self.assertEqual(area2['dates'][3]['total'], 1)
        self.assertEqual(area2['dates'][4]['date'], '12-09-2014')
        self.assertEqual(area2['dates'][4]['dayOfWeek'], 'Friday')
        self.assertEqual(area2['dates'][4]['positive'], 0)
        self.assertEqual(area2['dates'][4]['negative'], 1)
        self.assertEqual(area2['dates'][4]['total'], 1)
        self.assertEqual(area2['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area2['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area2['dates'][5]['positive'], 0)
        self.assertEqual(area2['dates'][5]['negative'], 1)
        self.assertEqual(area2['dates'][5]['total'], 1)

        area3 = response_json[2]
        self.assertEqual(area3['name'], self.area3.name)
        self.assertEqual(area3['totalReport'], 1)
        self.assertEqual(area3['positiveReport'], 1)
        self.assertEqual(area3['negativeReport'], 0)
        self.assertEqual(area3['dates'][0]['date'], '08-09-2014')
        self.assertEqual(area3['dates'][0]['dayOfWeek'], 'Monday')
        self.assertEqual(area3['dates'][0]['positive'], 0)
        self.assertEqual(area3['dates'][0]['negative'], 0)
        self.assertEqual(area3['dates'][0]['total'], 0)
        self.assertEqual(area3['dates'][1]['date'], '09-09-2014')
        self.assertEqual(area3['dates'][1]['dayOfWeek'], 'Tuesday')
        self.assertEqual(area3['dates'][1]['positive'], 1)
        self.assertEqual(area3['dates'][1]['negative'], 0)
        self.assertEqual(area3['dates'][1]['total'], 1)

    def test_api_summary_by_number_of_reports_with_staff_and_timezone(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)

        params = {'dates': '13/09/2014-13/09/2014', 'tz': 7}
        response = self.client.get(reverse('summary_by_number_of_report'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)
        response_json = order_list_by_id(response_json)

        area1 = response_json[0]
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['totalReport'], 0)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 0)
        self.assertEqual(area1['dates'][0]['date'], '13-09-2014')
        self.assertEqual(area1['dates'][0]['dayOfWeek'], 'Saturday')
        self.assertEqual(area1['dates'][0]['positive'], 0)
        self.assertEqual(area1['dates'][0]['negative'], 0)
        self.assertEqual(area1['dates'][0]['total'], 0)

        area2 = response_json[1]
        self.assertEqual(area2['name'], self.area2.name)
        self.assertEqual(area2['totalReport'], 1)
        self.assertEqual(area2['positiveReport'], 0)
        self.assertEqual(area2['negativeReport'], 1)
        self.assertEqual(area2['dates'][0]['date'], '13-09-2014')
        self.assertEqual(area2['dates'][0]['dayOfWeek'], 'Saturday')
        self.assertEqual(area2['dates'][0]['positive'], 0)
        self.assertEqual(area2['dates'][0]['negative'], 1)
        self.assertEqual(area2['dates'][0]['total'], 1)

        area3 = response_json[2]
        self.assertEqual(area3['name'], self.area3.name)
        self.assertEqual(area3['totalReport'], 0)
        self.assertEqual(area3['positiveReport'], 0)
        self.assertEqual(area3['negativeReport'], 0)
        self.assertEqual(area3['dates'][0]['date'], '13-09-2014')
        self.assertEqual(area3['dates'][0]['dayOfWeek'], 'Saturday')
        self.assertEqual(area3['dates'][0]['positive'], 0)
        self.assertEqual(area3['dates'][0]['negative'], 0)
        self.assertEqual(area3['dates'][0]['total'], 0)

    def test_api_summary_by_number_of_reports_with_user_all_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014'}
        response = self.client.get(reverse('summary_by_number_of_report'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)
        response_json = order_list_by_id(response_json)

        area1 = response_json[0]
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['totalReport'], 1)
        self.assertEqual(area1['positiveReport'], 1)
        self.assertEqual(area1['negativeReport'], 0)
        self.assertEqual(area1['dates'][1]['date'], '09-09-2014')
        self.assertEqual(area1['dates'][1]['dayOfWeek'], 'Tuesday')
        self.assertEqual(area1['dates'][1]['positive'], 0)
        self.assertEqual(area1['dates'][1]['negative'], 0)
        self.assertEqual(area1['dates'][1]['total'], 0)
        self.assertEqual(area1['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area1['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area1['dates'][5]['positive'], 1)
        self.assertEqual(area1['dates'][5]['negative'], 0)
        self.assertEqual(area1['dates'][5]['total'], 1)

        area2 = response_json[1]
        self.assertEqual(area2['name'], self.area2.name)
        self.assertEqual(area2['totalReport'], 3)
        self.assertEqual(area2['positiveReport'], 0)
        self.assertEqual(area2['negativeReport'], 3)
        self.assertEqual(area2['dates'][3]['date'], '11-09-2014')
        self.assertEqual(area2['dates'][3]['dayOfWeek'], 'Thursday')
        self.assertEqual(area2['dates'][3]['positive'], 0)
        self.assertEqual(area2['dates'][3]['negative'], 1)
        self.assertEqual(area2['dates'][3]['total'], 1)
        self.assertEqual(area2['dates'][4]['date'], '12-09-2014')
        self.assertEqual(area2['dates'][4]['dayOfWeek'], 'Friday')
        self.assertEqual(area2['dates'][4]['positive'], 0)
        self.assertEqual(area2['dates'][4]['negative'], 1)
        self.assertEqual(area2['dates'][4]['total'], 1)
        self.assertEqual(area2['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area2['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area2['dates'][5]['positive'], 0)
        self.assertEqual(area2['dates'][5]['negative'], 1)
        self.assertEqual(area2['dates'][5]['total'], 1)

        area3 = response_json[2]
        self.assertEqual(area3['name'], self.area3.name)
        self.assertEqual(area3['totalReport'], 1)
        self.assertEqual(area3['positiveReport'], 1)
        self.assertEqual(area3['negativeReport'], 0)
        self.assertEqual(area3['dates'][0]['date'], '08-09-2014')
        self.assertEqual(area3['dates'][0]['dayOfWeek'], 'Monday')
        self.assertEqual(area3['dates'][0]['positive'], 0)
        self.assertEqual(area3['dates'][0]['negative'], 0)
        self.assertEqual(area3['dates'][0]['total'], 0)
        self.assertEqual(area3['dates'][1]['date'], '09-09-2014')
        self.assertEqual(area3['dates'][1]['dayOfWeek'], 'Tuesday')
        self.assertEqual(area3['dates'][1]['positive'], 1)
        self.assertEqual(area3['dates'][1]['negative'], 0)
        self.assertEqual(area3['dates'][1]['total'], 1)

    def test_api_summary_by_number_of_reports_with_user_some_area(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014'}
        response = self.client.get(reverse('summary_by_number_of_report'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        area1 = response_json[0]
        self.assertEqual(area1['name'], self.area2.name)
        self.assertEqual(area1['totalReport'], 3)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 3)
        self.assertEqual(area1['dates'][3]['date'], '11-09-2014')
        self.assertEqual(area1['dates'][3]['dayOfWeek'], 'Thursday')
        self.assertEqual(area1['dates'][3]['positive'], 0)
        self.assertEqual(area1['dates'][3]['negative'], 1)
        self.assertEqual(area1['dates'][3]['total'], 1)
        self.assertEqual(area1['dates'][4]['date'], '12-09-2014')
        self.assertEqual(area1['dates'][4]['dayOfWeek'], 'Friday')
        self.assertEqual(area1['dates'][4]['positive'], 0)
        self.assertEqual(area1['dates'][4]['negative'], 1)
        self.assertEqual(area1['dates'][4]['total'], 1)
        self.assertEqual(area1['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area1['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area1['dates'][5]['positive'], 0)
        self.assertEqual(area1['dates'][5]['negative'], 1)
        self.assertEqual(area1['dates'][5]['total'], 1)

    def test_api_summary_by_number_of_reports_with_user_some_area_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014'}
        response = self.client.get(reverse('summary_by_number_of_report'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        area1 = response_json[0]
        self.assertEqual(area1['name'], self.area2.name)
        self.assertEqual(area1['totalReport'], 3)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 3)
        self.assertEqual(area1['dates'][3]['date'], '11-09-2014')
        self.assertEqual(area1['dates'][3]['dayOfWeek'], 'Thursday')
        self.assertEqual(area1['dates'][3]['positive'], 0)
        self.assertEqual(area1['dates'][3]['negative'], 1)
        self.assertEqual(area1['dates'][3]['total'], 1)
        self.assertEqual(area1['dates'][4]['date'], '12-09-2014')
        self.assertEqual(area1['dates'][4]['dayOfWeek'], 'Friday')
        self.assertEqual(area1['dates'][4]['positive'], 0)
        self.assertEqual(area1['dates'][4]['negative'], 1)
        self.assertEqual(area1['dates'][4]['total'], 1)
        self.assertEqual(area1['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area1['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area1['dates'][5]['positive'], 0)
        self.assertEqual(area1['dates'][5]['negative'], 1)
        self.assertEqual(area1['dates'][5]['total'], 1)

    def test_api_summary_by_number_of_reports_with_user_some_area_with_user_authority(self):
        tiffany = factory.create_user(username='Tiffany', status=USER_STATUS_VOLUNTEER)
        self.authority.users.add(tiffany)

        report1 = factory.create_report(created_by=tiffany, type=self.type2,
            administration_area=self.area1, incident_date=datetime.date(2014, 9, 13),
            date=datetime.datetime(2014, 9, 13, 0, 0, 0), negative=True)

        report2 = factory.create_report(created_by=tiffany, type=self.type2,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 11),
            date=datetime.datetime(2014, 9, 11, 0, 0, 0), negative=True)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014'}
        response = self.client.get(reverse('summary_by_number_of_report'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)
        response_json = order_list_by_id(response_json)

        area1 = response_json[0]
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['totalReport'], 2)
        self.assertEqual(area1['positiveReport'], 1)
        self.assertEqual(area1['negativeReport'], 1)
        self.assertEqual(area1['dates'][1]['date'], '09-09-2014')
        self.assertEqual(area1['dates'][1]['dayOfWeek'], 'Tuesday')
        self.assertEqual(area1['dates'][1]['positive'], 0)
        self.assertEqual(area1['dates'][1]['negative'], 0)
        self.assertEqual(area1['dates'][1]['total'], 0)
        self.assertEqual(area1['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area1['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area1['dates'][5]['positive'], 1)
        self.assertEqual(area1['dates'][5]['negative'], 1)
        self.assertEqual(area1['dates'][5]['total'], 2)

        area2 = response_json[1]
        self.assertEqual(area2['name'], self.area2.name)
        self.assertEqual(area2['totalReport'], 4)
        self.assertEqual(area2['positiveReport'], 0)
        self.assertEqual(area2['negativeReport'], 4)
        self.assertEqual(area2['dates'][3]['date'], '11-09-2014')
        self.assertEqual(area2['dates'][3]['dayOfWeek'], 'Thursday')
        self.assertEqual(area2['dates'][3]['positive'], 0)
        self.assertEqual(area2['dates'][3]['negative'], 2)
        self.assertEqual(area2['dates'][3]['total'], 2)
        self.assertEqual(area2['dates'][4]['date'], '12-09-2014')
        self.assertEqual(area2['dates'][4]['dayOfWeek'], 'Friday')
        self.assertEqual(area2['dates'][4]['positive'], 0)
        self.assertEqual(area2['dates'][4]['negative'], 1)
        self.assertEqual(area2['dates'][4]['total'], 1)
        self.assertEqual(area2['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area2['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area2['dates'][5]['positive'], 0)
        self.assertEqual(area2['dates'][5]['negative'], 1)
        self.assertEqual(area2['dates'][5]['total'], 1)

        area3 = response_json[2]
        self.assertEqual(area3['name'], self.area3.name)
        self.assertEqual(area3['totalReport'], 1)
        self.assertEqual(area3['positiveReport'], 1)
        self.assertEqual(area3['negativeReport'], 0)
        self.assertEqual(area3['dates'][0]['date'], '08-09-2014')
        self.assertEqual(area3['dates'][0]['dayOfWeek'], 'Monday')
        self.assertEqual(area3['dates'][0]['positive'], 0)
        self.assertEqual(area3['dates'][0]['negative'], 0)
        self.assertEqual(area3['dates'][0]['total'], 0)
        self.assertEqual(area3['dates'][1]['date'], '09-09-2014')
        self.assertEqual(area3['dates'][1]['dayOfWeek'], 'Tuesday')
        self.assertEqual(area3['dates'][1]['positive'], 1)
        self.assertEqual(area3['dates'][1]['negative'], 0)
        self.assertEqual(area3['dates'][1]['total'], 1)

    def test_api_summary_by_number_of_reports_with_user_some_area_with_authority_and_user_authority(self):
        tiffany = factory.create_user(username='Tiffany', status=USER_STATUS_VOLUNTEER)
        self.authority.users.add(tiffany)

        report1 = factory.create_report(created_by=tiffany, type=self.type2,
            administration_area=self.area1, incident_date=datetime.date(2014, 9, 13),
            date=datetime.datetime(2014, 9, 13, 0, 0, 0), negative=True)

        report2 = factory.create_report(created_by=tiffany, type=self.type2,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 11),
            date=datetime.datetime(2014, 9, 11, 0, 0, 0), negative=True)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014'}
        response = self.client.get(reverse('summary_by_number_of_report'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)
        response_json = order_list_by_id(response_json)

        area1 = response_json[0]
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['totalReport'], 2)
        self.assertEqual(area1['positiveReport'], 1)
        self.assertEqual(area1['negativeReport'], 1)
        self.assertEqual(area1['dates'][1]['date'], '09-09-2014')
        self.assertEqual(area1['dates'][1]['dayOfWeek'], 'Tuesday')
        self.assertEqual(area1['dates'][1]['positive'], 0)
        self.assertEqual(area1['dates'][1]['negative'], 0)
        self.assertEqual(area1['dates'][1]['total'], 0)
        self.assertEqual(area1['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area1['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area1['dates'][5]['positive'], 1)
        self.assertEqual(area1['dates'][5]['negative'], 1)
        self.assertEqual(area1['dates'][5]['total'], 2)

        area2 = response_json[1]
        self.assertEqual(area2['name'], self.area2.name)
        self.assertEqual(area2['totalReport'], 4)
        self.assertEqual(area2['positiveReport'], 0)
        self.assertEqual(area2['negativeReport'], 4)
        self.assertEqual(area2['dates'][3]['date'], '11-09-2014')
        self.assertEqual(area2['dates'][3]['dayOfWeek'], 'Thursday')
        self.assertEqual(area2['dates'][3]['positive'], 0)
        self.assertEqual(area2['dates'][3]['negative'], 2)
        self.assertEqual(area2['dates'][3]['total'], 2)
        self.assertEqual(area2['dates'][4]['date'], '12-09-2014')
        self.assertEqual(area2['dates'][4]['dayOfWeek'], 'Friday')
        self.assertEqual(area2['dates'][4]['positive'], 0)
        self.assertEqual(area2['dates'][4]['negative'], 1)
        self.assertEqual(area2['dates'][4]['total'], 1)
        self.assertEqual(area2['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area2['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area2['dates'][5]['positive'], 0)
        self.assertEqual(area2['dates'][5]['negative'], 1)
        self.assertEqual(area2['dates'][5]['total'], 1)

        area3 = response_json[2]
        self.assertEqual(area3['name'], self.area3.name)
        self.assertEqual(area3['totalReport'], 1)
        self.assertEqual(area3['positiveReport'], 1)
        self.assertEqual(area3['negativeReport'], 0)
        self.assertEqual(area3['dates'][0]['date'], '08-09-2014')
        self.assertEqual(area3['dates'][0]['dayOfWeek'], 'Monday')
        self.assertEqual(area3['dates'][0]['positive'], 0)
        self.assertEqual(area3['dates'][0]['negative'], 0)
        self.assertEqual(area3['dates'][0]['total'], 0)
        self.assertEqual(area3['dates'][1]['date'], '09-09-2014')
        self.assertEqual(area3['dates'][1]['dayOfWeek'], 'Tuesday')
        self.assertEqual(area3['dates'][1]['positive'], 1)
        self.assertEqual(area3['dates'][1]['negative'], 0)
        self.assertEqual(area3['dates'][1]['total'], 1)

    def test_api_summary_by_number_of_reports_with_user_some_area_with_user_authority_and_without_area(self):
        tiffany = factory.create_user(username='Tiffany', status=USER_STATUS_VOLUNTEER)
        self.authority.users.add(tiffany)

        report1 = factory.create_report(created_by=tiffany, type=self.type2,
            administration_area=self.area1, incident_date=datetime.date(2014, 9, 13),
            date=datetime.datetime(2014, 9, 13, 0, 0, 0), negative=True)

        report2 = factory.create_report(created_by=tiffany, type=self.type2,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 11),
            date=datetime.datetime(2014, 9, 11, 0, 0, 0), negative=True)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014'}
        response = self.client.get(reverse('summary_by_number_of_report'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        area1 = response_json[0]
        self.assertEqual(area1['name'], self.area2.name)
        self.assertEqual(area1['totalReport'], 4)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 4)
        self.assertEqual(area1['dates'][3]['date'], '11-09-2014')
        self.assertEqual(area1['dates'][3]['dayOfWeek'], 'Thursday')
        self.assertEqual(area1['dates'][3]['positive'], 0)
        self.assertEqual(area1['dates'][3]['negative'], 2)
        self.assertEqual(area1['dates'][3]['total'], 2)
        self.assertEqual(area1['dates'][4]['date'], '12-09-2014')
        self.assertEqual(area1['dates'][4]['dayOfWeek'], 'Friday')
        self.assertEqual(area1['dates'][4]['positive'], 0)
        self.assertEqual(area1['dates'][4]['negative'], 1)
        self.assertEqual(area1['dates'][4]['total'], 1)
        self.assertEqual(area1['dates'][5]['date'], '13-09-2014')
        self.assertEqual(area1['dates'][5]['dayOfWeek'], 'Saturday')
        self.assertEqual(area1['dates'][5]['positive'], 0)
        self.assertEqual(area1['dates'][5]['negative'], 1)
        self.assertEqual(area1['dates'][5]['total'], 1)

    def test_api_summary_by_number_of_reports_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('summary_by_number_of_report'))
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['dates'], 'Invalid dates. Please try again. (eg. 12/01/2015-18/01/2015)')

    def test_anonymous_cannot_access_api_summary_by_number_of_reports(self):
        response = self.client.get(reverse('summary_by_number_of_report'))
        self.assertEqual(response.status_code, 401)


class TestApiSummaryByInactivePerson(APITestCase):
    def setUp(self):
        call_command('clear_index', interactive=False, verbosity=0)
        
        factory.create_configuration(system='web.summary.minimum_reports', key='percent', value='20')

        self.taeyeon = factory.create_user(username='TaeYeon', last_name='Kim', project_mobile_number='0800000000', status=USER_STATUS_VOLUNTEER)
        self.jessica = factory.create_user(username='Jessica', last_name='Jung', project_mobile_number='0811111111', status=USER_STATUS_VOLUNTEER)
        self.yoona = factory.create_user(username='Yoona', last_name='Im', project_mobile_number='0822222222', is_staff=True)
        self.krystal = factory.create_user(username='Krystal', last_name='Jung', project_mobile_number='0833333333')
        self.tiffany = factory.create_user(username='Tiffany')

        self.authority = factory.create_authority()
        self.authority.users.add(self.tiffany)

        # authority [tiffany][report_type: 1,2][area: 1,2,3]
        # authority_1 [taeyeon, jessica][report_type: 1,2][area: 1,2]
        # authority_2 [krystal][report_type: 1,2][area: 3]

        self.type1 = factory.create_report_type(authority=self.authority)
        self.type2 = factory.create_report_type(authority=self.authority)

        self.authority_1 = factory.create_authority()
        self.authority_1.users.add(self.taeyeon)
        self.authority_1.users.add(self.jessica)
        self.area1 = factory.create_administration_area(authority=self.authority_1)
        self.area2 = factory.create_administration_area(authority=self.authority_1)

        self.authority_2 = factory.create_authority()
        self.authority_2.users.add(self.krystal)
        self.area3 = factory.create_administration_area(authority=self.authority_2)

        self.authority_1.inherits.add(self.authority)
        self.authority_2.inherits.add(self.authority)

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type2,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 9, 0, 0, 0), negative=True)
        self.report2 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area1, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 9, 22, 0, 0), negative=False)

    def test_api_summary_by_inactive_person_with_staff(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014', 'type': 'week'}
        response = self.client.get(reverse('summary_by_inactive_person'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        user1 = response_json[0]
        self.assertEqual(user1['administrationArea'], '')
        self.assertEqual(user1['parentAdministrationArea'], '')
        self.assertEqual(user1['fullName'], 'Jessica Jung')
        self.assertEqual(user1['status'], 'VOLUNTEER')
        self.assertEqual(user1['projectMobileNumber'], '0811111111')
        self.assertEqual(user1['totalReport'], 0)
        self.assertEqual(user1['percent'], 20)

    def test_api_summary_by_inactive_person_with_staff_and_timezone(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)

        params = {'dates': '08/09/2014-09/09/2014', 'type': 'week', 'tz': 7, 'percent': 60}
        response = self.client.get(reverse('summary_by_inactive_person'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        user1 = response_json[0]
        self.assertEqual(user1['administrationArea'], '')
        self.assertEqual(user1['parentAdministrationArea'], '')
        self.assertEqual(user1['fullName'], 'TaeYeon Kim')
        self.assertEqual(user1['projectMobileNumber'], '0800000000')
        self.assertEqual(user1['status'], 'VOLUNTEER')
        self.assertEqual(user1['totalReport'], 1)
        self.assertEqual(user1['percent'], 60)

        user2 = response_json[1]
        self.assertEqual(user2['administrationArea'], '')
        self.assertEqual(user2['parentAdministrationArea'], '')
        self.assertEqual(user2['fullName'], 'Jessica Jung')
        self.assertEqual(user2['projectMobileNumber'], '0811111111')
        self.assertEqual(user2['status'], 'VOLUNTEER')
        self.assertEqual(user2['totalReport'], 0)
        self.assertEqual(user2['percent'], 60)

        # user2 = response_json[1]
        # self.assertEqual(user2['administrationArea'], '')
        # self.assertEqual(user2['parentAdministrationArea'], '')
        # self.assertEqual(user2['fullName'], 'Krystal Jung')
        # self.assertEqual(user2['isVolunteer'], '')
        # self.assertEqual(user2['projectMobileNumber'], '0833333333')
        # self.assertEqual(user2['totalReport'], 0)
        # self.assertEqual(user2['percent'], 20)

    def test_api_summary_by_inactive_person_with_no_percent(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014', 'type': 'week'}
        response = self.client.get(reverse('summary_by_inactive_person'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        user1 = response_json[0]
        self.assertEqual(user1['administrationArea'], '')
        self.assertEqual(user1['parentAdministrationArea'], '')
        self.assertEqual(user1['fullName'], 'Jessica Jung')
        self.assertEqual(user1['status'], 'VOLUNTEER')
        self.assertEqual(user1['projectMobileNumber'], '0811111111')
        self.assertEqual(user1['totalReport'], 0)
        self.assertEqual(user1['percent'], 20)

    def test_api_summary_by_inactive_person_with_no_percent_and_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.tiffany.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014', 'type': 'week'}
        response = self.client.get(reverse('summary_by_inactive_person'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        user1 = response_json[0]
        self.assertEqual(user1['administrationArea'], '')
        self.assertEqual(user1['parentAdministrationArea'], '')
        self.assertEqual(user1['fullName'], 'Jessica Jung')
        self.assertEqual(user1['status'], 'VOLUNTEER')
        self.assertEqual(user1['projectMobileNumber'], '0811111111')
        self.assertEqual(user1['totalReport'], 0)
        self.assertEqual(user1['percent'], 20)

    def test_api_summary_by_inactive_person_with_no_percent_and_authority_and_user_authority(self):
        roykim = factory.create_user(username='SangWoo', last_name='Kim', project_mobile_number='0810101010', status=USER_STATUS_VOLUNTEER)
        self.authority.users.add(roykim)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.tiffany.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014', 'type': 'week'}
        response = self.client.get(reverse('summary_by_inactive_person'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        user1 = response_json[1]
        self.assertEqual(user1['administrationArea'], '')
        self.assertEqual(user1['parentAdministrationArea'], '')
        self.assertEqual(user1['fullName'], 'Jessica Jung')
        self.assertEqual(user1['status'], 'VOLUNTEER')
        self.assertEqual(user1['projectMobileNumber'], '0811111111')
        self.assertEqual(user1['totalReport'], 0)
        self.assertEqual(user1['percent'], 20)

        user2 = response_json[0]
        self.assertEqual(user2['administrationArea'], '')
        self.assertEqual(user2['parentAdministrationArea'], '')
        self.assertEqual(user2['fullName'], 'SangWoo Kim')
        self.assertEqual(user2['status'], 'VOLUNTEER')
        self.assertEqual(user2['projectMobileNumber'], '0810101010')
        self.assertEqual(user2['totalReport'], 0)
        self.assertEqual(user2['percent'], 20)

    def test_api_summary_by_inactive_person_with_percent(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014', 'type': 'week', 'percent': 60}
        response = self.client.get(reverse('summary_by_inactive_person'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        user1 = response_json[0]
        self.assertEqual(user1['administrationArea'], '')
        self.assertEqual(user1['parentAdministrationArea'], '')
        self.assertEqual(user1['fullName'], 'TaeYeon Kim')
        self.assertEqual(user1['projectMobileNumber'], '0800000000')
        self.assertEqual(user1['status'], 'VOLUNTEER')
        self.assertEqual(user1['totalReport'], 2)
        self.assertEqual(user1['percent'], 60)

        user2 = response_json[1]
        self.assertEqual(user2['administrationArea'], '')
        self.assertEqual(user2['parentAdministrationArea'], '')
        self.assertEqual(user2['fullName'], 'Jessica Jung')
        self.assertEqual(user2['projectMobileNumber'], '0811111111')
        self.assertEqual(user2['status'], 'VOLUNTEER')
        self.assertEqual(user2['totalReport'], 0)
        self.assertEqual(user2['percent'], 60)

    def test_api_summary_by_inactive_person_with_percent_and_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.tiffany.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014', 'type': 'week', 'percent': 60}
        response = self.client.get(reverse('summary_by_inactive_person'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        user1 = response_json[0]
        self.assertEqual(user1['administrationArea'], '')
        self.assertEqual(user1['parentAdministrationArea'], '')
        self.assertEqual(user1['fullName'], 'TaeYeon Kim')
        self.assertEqual(user1['projectMobileNumber'], '0800000000')
        self.assertEqual(user1['status'], 'VOLUNTEER')
        self.assertEqual(user1['totalReport'], 2)
        self.assertEqual(user1['percent'], 60)

        user2 = response_json[1]
        self.assertEqual(user2['administrationArea'], '')
        self.assertEqual(user2['parentAdministrationArea'], '')
        self.assertEqual(user2['fullName'], 'Jessica Jung')
        self.assertEqual(user2['projectMobileNumber'], '0811111111')
        self.assertEqual(user2['status'], 'VOLUNTEER')
        self.assertEqual(user2['totalReport'], 0)
        self.assertEqual(user2['percent'], 60)

    def test_api_summary_by_inactive_person_with_percent_and_authority_and_user_authority(self):
        roykim = factory.create_user(username='SangWoo', last_name='Kim', project_mobile_number='0810101010', status=USER_STATUS_VOLUNTEER)
        self.authority.users.add(roykim)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.tiffany.auth_token.key)

        params = {'dates': '08/09/2014-14/09/2014', 'type': 'week', 'percent': 60}
        response = self.client.get(reverse('summary_by_inactive_person'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

        user1 = response_json[0]
        self.assertEqual(user1['administrationArea'], '')
        self.assertEqual(user1['parentAdministrationArea'], '')
        self.assertEqual(user1['fullName'], 'TaeYeon Kim')
        self.assertEqual(user1['projectMobileNumber'], '0800000000')
        self.assertEqual(user1['status'], 'VOLUNTEER')
        self.assertEqual(user1['totalReport'], 2)
        self.assertEqual(user1['percent'], 60)

        user2 = response_json[1]
        self.assertEqual(user2['administrationArea'], '')
        self.assertEqual(user2['parentAdministrationArea'], '')
        self.assertEqual(user2['fullName'], 'Jessica Jung')
        self.assertEqual(user2['projectMobileNumber'], '0811111111')
        self.assertEqual(user2['status'], 'VOLUNTEER')
        self.assertEqual(user2['totalReport'], 0)
        self.assertEqual(user2['percent'], 60)

        user3 = response_json[2]
        self.assertEqual(user3['administrationArea'], '')
        self.assertEqual(user3['parentAdministrationArea'], '')
        self.assertEqual(user3['fullName'], 'SangWoo Kim')
        self.assertEqual(user3['status'], 'VOLUNTEER')
        self.assertEqual(user3['projectMobileNumber'], '0810101010')
        self.assertEqual(user3['totalReport'], 0)
        self.assertEqual(user3['percent'], 60)

    def test_api_summary_by_inactive_person_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('summary_by_inactive_person'))
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['dates'], 'Invalid dates. Please try again. (eg. 12/01/2015-18/01/2015)')

    def test_anonymous_cannot_access_api_summary_by_inactive_person(self):
        response = self.client.get(reverse('summary_by_inactive_person'))
        self.assertEqual(response.status_code, 401)


class TestApiSummaryByShowDetail(APITestCase):
    def setUp(self):
        call_command('clear_index', interactive=False, verbosity=0)
        
        factory.create_configuration(system='web.summary.minimum_reports', key='percent', value='20')

        self.taeyeon = factory.create_user(status=USER_STATUS_VOLUNTEER)
        self.jessica = factory.create_user(status=USER_STATUS_VOLUNTEER)
        self.yoona = factory.create_user(is_staff=True)
        self.krystal = factory.create_user()
        self.tiffany = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.tiffany)

        self.type1 = factory.create_report_type(name=u'สัตว์ป่า', authority=self.authority)
        self.type2 = factory.create_report_type(name=u'สัตว์ป่วย/ตาย', authority=self.authority)
        self.type3 = factory.create_report_type(name=u'สัตว์กัด', authority=self.authority)
        self.type4 = factory.create_report_type(name=u'อื่นๆ', authority=self.authority)

        self.authority_1 = factory.create_authority()
        self.authority_1.users.add(self.taeyeon)
        self.authority_1.users.add(self.jessica)
        self.authority_1.users.add(self.krystal)
        self.area1 = factory.create_administration_area(name='Seoul', authority=self.authority_1)
        self.area2 = factory.create_administration_area(name='Tokyo', authority=self.authority_1)
        self.area3 = factory.create_administration_area(name='London', authority=self.authority_1)
        self.area3_1 = self.area3.add_child(name='Stamford', location=self.area3.location, authority=self.authority_1)
        self.area3_2 = self.area3.add_child(name='Wembley', location=self.area3.location, authority=self.authority_1)

        self.authority_1.inherits.add(self.authority)

        self.report1 = factory.create_report(created_by=self.taeyeon, type=self.type2,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 1, 15, 0, 0), negative=True, 
            form_data={
                "symptom": "cough,fever,pain",
                "animalType": u"โคนม",
                "sickCount": 4,
                "deathCount": 0,
                "totalCount": 4,
                "nearByCount": 1,
            })
        self.report2 = factory.create_report(created_by=self.taeyeon, type=self.type2,
            administration_area=self.area1, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 2, 5, 0, 0), negative=True, 
            form_data={
                "symptom": "cough,fever,pain",
                "animalType": u"วัว",
                "sickCount": 2,
                "deathCount": 2,
                "totalCount": 4,
                "nearByCount": 1,
            })
        self.report3 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area1, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 3, 7, 0, 0), negative=False) 
        self.report4 = factory.create_report(created_by=self.taeyeon, type=self.type1,
            administration_area=self.area1, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 4, 12, 0, 0), negative=False) 
        self.report5 = factory.create_report(created_by=self.jessica, type=self.type1,
            administration_area=self.area1, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 5, 20, 0, 0), negative=False)
        self.report6 = factory.create_report(created_by=self.jessica, type=self.type3,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 6, 10, 0, 0), negative=True,
            form_data={
                "animalType": u"หมา",
            }) 
        self.report7 = factory.create_report(created_by=self.krystal, type=self.type3,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 9), 
            date=datetime.datetime(2014, 9, 7, 10, 0, 0), negative=True,
            form_data={
                "animalType": u"หมา",
            }) 
        self.report8 = factory.create_report(created_by=self.jessica, type=self.type3,
        administration_area=self.area2, incident_date=datetime.date(2014, 9, 9), 
        date=datetime.datetime(2014, 9, 6, 11, 0, 0), negative=True,
        form_data={
            "animalType": u"หมา",
        })
        self.report9 = factory.create_report(created_by=self.jessica, type=self.type3,
        administration_area=self.area2, incident_date=datetime.date(2014, 9, 9), 
        date=datetime.datetime(2014, 9, 6, 9, 0, 0), negative=True,
        form_data={
            "animalType": u"หมา",
        }) 
        self.report10 = factory.create_report(created_by=self.jessica, type=self.type4,
        administration_area=self.area2, incident_date=datetime.date(2014, 9, 20), 
        date=datetime.datetime(2014, 9, 20, 13, 0, 0), negative=True)

    def test_api_summary_by_show_detail_with_staff(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)

        params = {'month': '09/2014', 'administrationAreaId': self.area1.id, 'force': True}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)

        area1 = response_json
        self.assertEqual(area1['name'], self.area1.name)
        self.assertEqual(area1['totalReport'], 4)
        self.assertEqual(area1['positiveReport'], 3)
        self.assertEqual(area1['negativeReport'], 1)
        self.assertEqual(area1['animalTypes'][0]['name'], u'วัว')
        self.assertEqual(area1['animalTypes'][0]['sick'], 2)
        self.assertEqual(area1['animalTypes'][0]['death'], 2)
        self.assertEqual(area1['animalTypes'][0]['total'], 4)
        self.assertEqual(area1['animalTypes'][0]['nearBy'], 1)
        self.assertEqual(area1['reportTypes'][0]['name'], self.type1.name)
        self.assertEqual(area1['reportTypes'][0]['totalReport'], 3)
        self.assertEqual(area1['reportTypes'][1]['name'], self.type2.name)
        self.assertEqual(area1['reportTypes'][1]['totalReport'], 1)
        self.assertEqual(area1['reportTypes'][2]['name'], self.type3.name)
        self.assertEqual(area1['reportTypes'][2]['totalReport'], 0)
        self.assertEqual(area1['timeRanges'][0]['totalReport'], 1)
        self.assertEqual(area1['timeRanges'][1]['totalReport'], 1)
        self.assertEqual(area1['timeRanges'][2]['totalReport'], 1)
        self.assertEqual(area1['timeRanges'][3]['totalReport'], 1)
        self.assertEqual(area1['grade'], 'B')

    def test_api_summary_by_show_detail_with_not_staff_choose_leaf_node_that_have_no_parent(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        params = {'month': '09/2014', 'administrationAreaId': self.area2.id, 'force': True}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)

        area1 = response_json
        self.assertEqual(area1['name'], self.area2.name)
        self.assertEqual(area1['totalReport'], 6)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 6)

        self.assertEqual(len(area1['animalTypes']), 2)

        self.assertEqual(area1['reportTypes'][0]['name'], self.type1.name)
        self.assertEqual(area1['reportTypes'][0]['totalReport'], 0)
        self.assertEqual(area1['reportTypes'][1]['name'], self.type2.name)
        self.assertEqual(area1['reportTypes'][1]['totalReport'], 1)
        self.assertEqual(area1['reportTypes'][2]['name'], self.type3.name)
        self.assertEqual(area1['reportTypes'][2]['totalReport'], 4)

        self.assertEqual(area1['timeRanges'][0]['totalReport'], 0)
        self.assertEqual(area1['timeRanges'][1]['totalReport'], 4)
        self.assertEqual(area1['timeRanges'][2]['totalReport'], 2)
        self.assertEqual(area1['timeRanges'][3]['totalReport'], 0)
        self.assertEqual(area1['grade'], 'B')

    def test_api_summary_by_show_detail_with_not_staff_choose_leaf_node_that_have_no_parent_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.tiffany.auth_token.key)

        params = {'month': '09/2014', 'administrationAreaId': self.area2.id, 'force': True}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)

        area1 = response_json
        self.assertEqual(area1['name'], self.area2.name)
        self.assertEqual(area1['totalReport'], 6)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 6)

        self.assertEqual(len(area1['animalTypes']), 2)

        self.assertEqual(area1['reportTypes'][0]['name'], self.type1.name)
        self.assertEqual(area1['reportTypes'][0]['totalReport'], 0)
        self.assertEqual(area1['reportTypes'][1]['name'], self.type2.name)
        self.assertEqual(area1['reportTypes'][1]['totalReport'], 1)
        self.assertEqual(area1['reportTypes'][2]['name'], self.type3.name)
        self.assertEqual(area1['reportTypes'][2]['totalReport'], 4)

        self.assertEqual(area1['timeRanges'][0]['totalReport'], 0)
        self.assertEqual(area1['timeRanges'][1]['totalReport'], 4)
        self.assertEqual(area1['timeRanges'][2]['totalReport'], 2)
        self.assertEqual(area1['timeRanges'][3]['totalReport'], 0)
        self.assertEqual(area1['grade'], 'B')

    def test_api_summary_by_show_detail_with_not_staff_choose_leaf_node_that_have_no_parent_with_authority_and_user_authority(self):
        roykim = factory.create_user(username='SangWoo', last_name='Kim', project_mobile_number='0810101010', status=USER_STATUS_VOLUNTEER)
        self.authority.users.add(roykim)

        report = factory.create_report(created_by=roykim, type=self.type2,
            administration_area=self.area2, incident_date=datetime.date(2014, 9, 9),
            date=datetime.datetime(2014, 9, 6, 10, 0, 0), negative=True,
            form_data={
                "symptom": "cough,fever,pain",
                "animalType": u"วัว",
                "sickCount": 2,
                "deathCount": 0,
                "totalCount": 2,
                "nearByCount": 1,
            })

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.tiffany.auth_token.key)

        params = {'month': '09/2014', 'administrationAreaId': self.area2.id, 'force': True}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)

        area1 = response_json
        self.assertEqual(area1['name'], self.area2.name)
        self.assertEqual(area1['totalReport'], 7)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 7)

        self.assertEqual(len(area1['animalTypes']), 3)

        self.assertEqual(area1['reportTypes'][0]['name'], self.type1.name)
        self.assertEqual(area1['reportTypes'][0]['totalReport'], 0)
        self.assertEqual(area1['reportTypes'][1]['name'], self.type2.name)
        self.assertEqual(area1['reportTypes'][1]['totalReport'], 2)
        self.assertEqual(area1['reportTypes'][2]['name'], self.type3.name)
        self.assertEqual(area1['reportTypes'][2]['totalReport'], 4)

        self.assertEqual(area1['timeRanges'][0]['totalReport'], 0)
        self.assertEqual(area1['timeRanges'][1]['totalReport'], 5)
        self.assertEqual(area1['timeRanges'][2]['totalReport'], 2)
        self.assertEqual(area1['timeRanges'][3]['totalReport'], 0)
        self.assertEqual(area1['grade'], 'A')

    def test_api_summary_by_show_detail_with_not_staff_choose_leaf_node_that_have_parent(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        params = {'month': '09/2014', 'administrationAreaId': self.area3_2.id, 'force': True}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        area1 = response_json

        self.assertEqual(area1['name'], self.area3_2.name)
        self.assertEqual(area1['totalReport'], 0)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 0)
        self.assertEqual(area1['grade'], 'C')

    def test_api_summary_by_show_detail_with_not_staff_choose_leaf_node_that_have_parent_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.tiffany.auth_token.key)

        params = {'month': '09/2014', 'administrationAreaId': self.area3_2.id, 'force': True}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        area1 = response_json

        self.assertEqual(area1['name'], self.area3_2.name)
        self.assertEqual(area1['totalReport'], 0)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 0)
        self.assertEqual(area1['grade'], 'C')

    def test_api_summary_by_show_detail_with_not_staff_choose_leaf_node_that_have_parent_with_authority_and_user_authority(self):
        roykim = factory.create_user(username='SangWoo', last_name='Kim', project_mobile_number='0810101010', status=USER_STATUS_VOLUNTEER)
        self.authority.users.add(roykim)

        report = factory.create_report(created_by=roykim, type=self.type2,
            administration_area=self.area3_2, incident_date=datetime.date(2014, 9, 9),
            date=datetime.datetime(2014, 9, 6, 10, 0, 0), negative=True,
            form_data={
                "symptom": "cough,fever,pain",
                "animalType": u"วัว",
                "sickCount": 2,
                "deathCount": 0,
                "totalCount": 2,
                "nearByCount": 1,
            })

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.tiffany.auth_token.key)

        params = {'month': '09/2014', 'administrationAreaId': self.area3_2.id, 'force': True}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        area1 = response_json

        self.assertEqual(area1['name'], self.area3_2.name)
        self.assertEqual(area1['totalReport'], 1)
        self.assertEqual(area1['positiveReport'], 0)
        self.assertEqual(area1['negativeReport'], 1)
        self.assertEqual(area1['grade'], 'C')

    def test_api_summary_by_show_detail_adminintration_area_not_leaf_node(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {'month': '09/2014', 'administrationAreaId': self.area3.id}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['administrationAreaId'], 'Invalid administrationAreaId. administrationAreaId must be leaf node.')

    def test_api_summary_by_show_detail_adminintration_area_not_exist(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {'month': '09/2014', 'administrationAreaId': 99999}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['administrationAreaId'], 'Invalid administrationAreaId. administrationAreaId does not exist.')

    def test_api_summary_by_show_detail_adminintration_area_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {'month': '09/2014'}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['administrationAreaId'], 'administrationAreaId is required.')

    def test_api_summary_by_show_detail_dates_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {'administrationAreaId': self.area1.id}
        response = self.client.get(reverse('summary_by_show_area_detail'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['month'], 'Invalid month. Please try again. (eg. 1/2015)')

    def test_anonymous_cannot_access_api_summary_by_show_detail(self):
        response = self.client.get(reverse('summary_by_show_area_detail'))
        self.assertEqual(response.status_code, 401)

