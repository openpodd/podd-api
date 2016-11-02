# -*- encoding: utf-8 -*-

import datetime
import json

from mock import patch

from django.conf import settings
from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase

from common import factory
from common.constants import NEWS_TYPE_NEWS
from common.functions import clean_phone_numbers, clean_emails
from notifications.models import Notification


class TestAPINotificationSeen(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user()
        self.report = factory.create_report()
        self.notification1 = factory.create_notification(report=self.report, receive_user=self.taeyeon)
        self.notification2 = factory.create_notification(report=self.report, receive_user=self.taeyeon)

    def test_anonymous_cannot_access_api_seen_notification(self):
        params = {'notificationId': self.notification2.id }
        response = self.client.post(reverse('notification-seen'), params)
        self.assertEqual(response.status_code, 401)

    def test_api_seen_notification(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {'notificationId': self.notification1.id }
        response = self.client.post(reverse('notification-seen'), params)
        self.assertEqual(response.status_code, 200)

        notification1 = Notification.objects.get(id=self.notification1.id)
        self.assertNotEqual(notification1.seen_at, None)

'''
class TestAPINotification(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(is_staff=True)
        self.jessica = factory.create_user()
        self.report = factory.create_report()
        self.notification = factory.create_notification()

    def test_staff_post_api_create_notification(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'report': self.report.id,
            'message': 'All of this.',
            'type': NEWS_TYPE_NEWS,
            'receiveUser': self.jessica.id,
        }
        response = self.client.post(reverse('notification-list'), params)
        self.assertEqual(response.status_code, 405)

        response_json = json.loads(response.content)
        self.assertTrue(response_json['report'])
        self.assertEqual(response_json['report'], self.report.id)
        self.assertEqual(response_json['message'], 'All of this.')
        self.assertEqual(response_json['type'], NEWS_TYPE_NEWS)
        self.assertEqual(response_json['receiveUser'], self.jessica.id)

        notification = Notification.objects.latest('id')
        self.assertEqual(notification.report, self.report)
        self.assertEqual(notification.message, 'All of this.')
        self.assertEqual(notification.type, NEWS_TYPE_NEWS)
        self.assertEqual(notification.receive_user, self.jessica)
        self.assertFalse(notification.seen_at)

    def test_gen_user_cannot_access_api_notification_create(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.post(reverse('notification-list'))
        self.assertEqual(response.status_code, 405)

    def test_staff_cannot_access_api_notification_list(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('notification-list'))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_api_notification_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('notification-detail', args=[self.notification.id]))
        #self.assertEqual(response.status_code, 405)

    def test_staff_cannot_access_api_notification_edit(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.put(reverse('notification-detail', args=[self.notification.id]))
        self.assertEqual(response.status_code, 405)

    def test_staff_cannot_access_api_notification_view(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.delete(reverse('notification-detail', args=[self.notification.id]))
        self.assertEqual(response.status_code, 405)

    def test_staff_cannot_access_api_notification_delete(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('notification-detail', args=[self.notification.id]))
        #self.assertEqual(response.status_code, 405)
'''


def mock_test_send_notification(type, users, subject='[test]', message='test send notification.'):
    return []


class TestAPINotificationTest(APITestCase):

    def setUp(self):
        self.taeyeon = factory.create_user()

    def test_anonymous_cannot_send_test_notification(self):
        params = {}
        response = self.client.post(reverse('notification-test'), params)
        self.assertEqual(response.status_code, 401)

    def test_api_send_notification_with_no_user(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'message': '[test] test-SMS'
        }
        response = self.client.post(reverse('notification-test'), params)
        self.assertEqual(response.status_code, 400)

    def test_api_send_notification_with_no_message(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'users': 'yoona 089-12345678',
        }
        response = self.client.post(reverse('notification-test'), params)
        self.assertEqual(response.status_code, 400)

    @patch('notifications.tasks.test_send_notification.delay', mock_test_send_notification)
    def test_api_send_notification(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'users': 'yoona 089-12345678',
            'message': '[test] test-SMS'
        }
        response = self.client.post(reverse('notification-test'), params)
        self.assertEqual(response.status_code, 200)
