# -*- encoding: utf-8 -*-
import json

from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase

from common import factory
from common.constants import GROUP_WORKING_TYPE_REPORT_TYPE, GROUP_WORKING_TYPE_ADMINSTRATION_AREA
from mentions.models import Mention


class TestApiMentionList(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.yoona = factory.create_user()
        self.krystal = factory.create_user()

        self.authority = factory.create_authority()
        self.authority.users.add(self.taeyeon)
        self.authority.users.add(self.jessica)
        self.authority.users.add(self.yoona)
        self.authority.users.add(self.krystal)

        self.type = factory.create_report_type(authority=self.authority)
        self.area = factory.create_administration_area(authority=self.authority)

        self.report = factory.create_report(created_by=self.taeyeon, type=self.type,
                administration_area=self.area)
    
    def test_get_api_mention_list(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello @[%s] @[%s]" % (self.taeyeon.username, self.jessica.username)
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Ayo GG @[%s] @[%s]" % (self.taeyeon.username, self.jessica.username)
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('mention-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        mention1 = response_json[0]
        self.assertEqual(mention1['mentioner']['username'], '%s' % self.yoona.username)
        self.assertEqual(mention1['mentionee']['username'], '%s' % self.jessica.username)
        self.assertEqual(mention1['isNotified'], False)
        self.assertEqual(mention1['seenAt'], None)

        mention2 = response_json[1]
        self.assertEqual(mention2['mentioner']['username'], '%s' % self.taeyeon.username)
        self.assertEqual(mention2['mentionee']['username'], '%s' % self.jessica.username)
        self.assertEqual(mention2['isNotified'], False)
        self.assertEqual(mention2['seenAt'], None)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('mention-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

        mention3 = response_json[0]
        self.assertEqual(mention3['mentioner']['username'], '%s' % self.yoona.username)
        self.assertEqual(mention3['mentionee']['username'], '%s' % self.taeyeon.username)
        self.assertEqual(mention3['isNotified'], False)
        self.assertEqual(mention3['seenAt'], None)

        mention4 = response_json[1]
        self.assertEqual(mention4['mentioner']['username'], '%s' % self.taeyeon.username)
        self.assertEqual(mention4['mentionee']['username'], '%s' % self.taeyeon.username)
        self.assertEqual(mention4['isNotified'], True)
        self.assertEqual(mention4['seenAt'], None)

    def test_get_api_mention_list_with_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Hello @[%s] @[%s]" % (self.krystal.username, self.jessica.username)
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Ayo GG @[%s] @[%s]" % (self.krystal.username, self.jessica.username)
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('mention-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        mention1 = response_json[0]
        self.assertEqual(mention1['mentioner']['username'], '%s' % self.yoona.username)
        self.assertEqual(mention1['mentionee']['username'], '%s' % self.jessica.username)
        self.assertEqual(mention1['isNotified'], False)
        self.assertEqual(mention1['seenAt'], None)

        mention2 = response_json[1]
        self.assertEqual(mention2['mentioner']['username'], '%s' % self.krystal.username)
        self.assertEqual(mention2['mentionee']['username'], '%s' % self.jessica.username)
        self.assertEqual(mention2['isNotified'], False)
        self.assertEqual(mention2['seenAt'], None)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.krystal.auth_token.key)
        response = self.client.get(reverse('mention-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        mention3 = response_json[0]
        self.assertEqual(mention3['mentioner']['username'], '%s' % self.yoona.username)
        self.assertEqual(mention3['mentionee']['username'], '%s' % self.krystal.username)
        self.assertEqual(mention3['isNotified'], False)
        self.assertEqual(mention3['seenAt'], None)

        mention4 = response_json[1]
        self.assertEqual(mention4['mentioner']['username'], '%s' % self.krystal.username)
        self.assertEqual(mention4['mentionee']['username'], '%s' % self.krystal.username)
        self.assertEqual(mention4['isNotified'], True)
        self.assertEqual(mention4['seenAt'], None)

    def test_post_api_mention_seen_with_mentionee(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Ayo GG @[%s]" % self.jessica.username
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        
        mention = Mention.objects.latest('id')
        params = {
            "mentionId": mention.id,
        }

        response = self.client.post(reverse('mention-seen'), params)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('mention-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        mention1 = response_json[0]
        self.assertEqual(mention1['mentioner']['username'], '%s' % self.yoona.username)
        self.assertEqual(mention1['mentionee']['username'], '%s' % self.jessica.username)
        self.assertEqual(mention1['isNotified'], True)
        self.assertNotEqual(mention1['seenAt'], None)

    def test_post_api_mention_seen_without_mentionee(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            "reportId": self.report.id,
            "message": "Ayo GG @[%s]" % self.jessica.username
        }
        response = self.client.post(reverse('reportcomment-list'), params)
        self.assertEqual(response.status_code, 201)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        
        mention = Mention.objects.latest('id')
        params = {
            "mentionId": mention.id,
        }

        response = self.client.post(reverse('mention-seen'), params)
        self.assertEqual(response.status_code, 404)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('mention-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        mention1 = response_json[0]
        self.assertEqual(mention1['mentioner']['username'], '%s' % self.yoona.username)
        self.assertEqual(mention1['mentionee']['username'], '%s' % self.jessica.username)
        self.assertEqual(mention1['isNotified'], False)
        self.assertEqual(mention1['seenAt'], None)

