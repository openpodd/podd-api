import calendar
import json
import datetime

from django_redis import get_redis_connection
from mock import patch
from mockredis import mock_strict_redis_client

from django.core.urlresolvers import reverse
from django.contrib.gis.geos import GEOSGeometry
from rest_framework.test import APITestCase

from accounts.models import Authority
from common import factory
from common.constants import USER_STATUS_ADDITION_VOLUNTEER
from common.models import get_current_domain_id
from feed.functions import warm_cache_public_feed
from reports.models import AdministrationArea


def feedSetUp(self):
    current_domain_id = get_current_domain_id()
    # self.private_authority = Authority.objects.create(name='Private Authority', code='private_authority')
    # self.private_report_type = factory.create_report_type(authority=self.private_authority)
    self.public_authority = Authority.objects.create(name='public_%d' % current_domain_id, code='public_%d' % current_domain_id)
    self.public_report_type = factory.create_report_type(authority=self.public_authority)
    self.private_user = factory.create_user(
        username="mr_private",
        status=USER_STATUS_ADDITION_VOLUNTEER,
        is_anonymous=False,
        is_public=False
    )
    self.public_user = factory.create_user(
        username="mr_public",
        status=USER_STATUS_ADDITION_VOLUNTEER,
        is_anonymous=False,
        is_public=True
    )
    self.public_authority.users.add(self.public_user)
    mpoly_str = '''
    {
        "type": "MultiPolygon",
        "coordinates": [[
          [
            [
              94.5703125,
              5.61598581915534
            ],
            [
              94.5703125,
              23.563987128451217
            ],
            [
              108.6328125,
              23.563987128451217
            ],
            [
              108.6328125,
              5.61598581915534
            ],
            [
              94.5703125,
              5.61598581915534
            ]
          ]
        ]]
    }
    '''
    location_str = '''
    {
        "type": "Point",
        "coordinates": [
          101.953125,
          14.604847155053898
        ]
    }
    '''
    self.administration_area_mpoly = GEOSGeometry(mpoly_str)
    self.administration_area_location = GEOSGeometry(location_str)
    self.public_admin_area = AdministrationArea.objects.create(
        name="admin_area1",
        mpoly=self.administration_area_mpoly,
        location=self.administration_area_location,
        authority=self.public_authority,
    )
    # self.private_admin_area = AdministrationArea.objects.create(
    #     name="private_admin_area",
    #     location=self.administration_area_location,
    #     authority=self.private_authority,
    # )

    redis = get_redis_connection()
    ''':type redis: redis.StrictRedis'''
    redis.flushall()

    self.report1 = factory.create_report(
        created_by=self.public_user,
        type=self.public_report_type,
        administration_area=self.public_admin_area
    )
    self.report1.created_at = self.report1.created_at - datetime.timedelta(hours=1)
    self.report1.save()
    self.report2 = factory.create_report(
        created_by=self.public_user,
        type=self.public_report_type,
        administration_area=self.public_admin_area
    )
    self.report3 = factory.create_report(
        created_by=self.public_user,
        type=self.public_report_type,
        administration_area=self.public_admin_area
    )
    self.report3.created_at = self.report3.created_at - datetime.timedelta(hours=2)
    self.report3.save()
    self.report4 = factory.create_report(
        created_by=self.public_user,
        type=self.public_report_type,
        administration_area=self.public_admin_area
    )
    self.report4.created_at = self.report4.created_at - datetime.timedelta(hours=3)
    self.report4.save()


@patch('django_redis.get_redis_connection', mock_strict_redis_client)
class TestAPI(APITestCase):
    def setUp(self):
        feedSetUp(self)

    def test_get_public_feed(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.public_user.auth_token.key)

        query_params = {
            "administrationArea": self.public_authority.id,
        }
        response = self.client.get(reverse('feed_list'), data=query_params)
        self.assertEqual(response.status_code, 200)

        response_obj = json.loads(response.content)
        self.assertEqual(len(response_obj['results']), 4)
        self.assertEqual(response_obj['results'][0]['id'], self.report2.id)
        self.assertEqual(response_obj['results'][1]['id'], self.report1.id)
        self.assertEqual(response_obj['results'][2]['id'], self.report3.id)
        self.assertEqual(response_obj['results'][3]['id'], self.report4.id)

        # try to provide `createdAt__gt` and `createdAt__lt`
        query_params = {
            "administrationArea": self.public_authority.id,
            "createdAt__lt": datetime.datetime.now() - datetime.timedelta(hours=1, minutes=30),
            "createdAt__gt": datetime.datetime.now() - datetime.timedelta(hours=3, minutes=30),
        }

        response = self.client.get(reverse('feed_list'), data=query_params)
        self.assertEqual(response.status_code, 200)

        response_obj = json.loads(response.content)
        self.assertEqual(len(response_obj['results']), 2)
        self.assertEqual(response_obj['results'][0]['id'], self.report3.id)
        self.assertEqual(response_obj['results'][1]['id'], self.report4.id)

        # # add curated report
        # curated_report = factory.create_report(
        #     created_by=self.private_user,
        #     type=self.private_report_type,
        #     administration_area=self.private_admin_area,
        # )
        # curated_report.curate_in_administration_area(self.public_admin_area)
        #
        # response = self.client.get(reverse('feed_list'), data=query_params)
        # self.assertEqual(response.status_code, 200)
        # response_obj = json.loads(response.content)
        # self.assertEqual(len(response_obj['results']), 5)

    def test_warm_cache_public_feed(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.public_user.auth_token.key)

        redis = get_redis_connection()
        ''':type redis: redis.StrictRedis'''
        redis.flushall()

        # add curated report

        warm_cache_public_feed()

        query_params = {
            "administrationArea": self.public_authority.id,
        }
        response = self.client.get(reverse('feed_list'), data=query_params)
        self.assertEqual(response.status_code, 200)

        response_obj = json.loads(response.content)
        self.assertEqual(len(response_obj['results']), 4)
        self.assertEqual(response_obj['results'][0]['id'], self.report2.id)
        self.assertEqual(response_obj['results'][1]['id'], self.report1.id)
        self.assertEqual(response_obj['results'][2]['id'], self.report3.id)
        self.assertEqual(response_obj['results'][3]['id'], self.report4.id)

    def test_get_own_feed(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.public_user.auth_token.key)

        another_user = factory.create_user(
            username="mr_another_public",
            status=USER_STATUS_ADDITION_VOLUNTEER,
            is_anonymous=False,
            is_public=True
        )
        factory.create_report(
            created_by=another_user,
            type=self.public_report_type,
            administration_area=self.public_admin_area
        )

        response = self.client.get(reverse('feed_list_mine'))
        self.assertEqual(response.status_code, 200)

        response_obj = json.loads(response.content)
        self.assertEqual(len(response_obj['results']), 4)
        self.assertEqual(response_obj['results'][0]['id'], self.report2.id)
        self.assertEqual(response_obj['results'][1]['id'], self.report1.id)
        self.assertEqual(response_obj['results'][2]['id'], self.report3.id)
        self.assertEqual(response_obj['results'][3]['id'], self.report4.id)

        # try to provide `createdAt__gt` and `createdAt__lt`
        query_params = {
            "createdAt__lt": datetime.datetime.now() - datetime.timedelta(hours=1, minutes=30),
            "createdAt__gt": datetime.datetime.now() - datetime.timedelta(hours=3, minutes=30),
        }

        response = self.client.get(reverse('feed_list_mine'), data=query_params)
        self.assertEqual(response.status_code, 200)

        response_obj = json.loads(response.content)
        self.assertEqual(len(response_obj['results']), 2)
        self.assertEqual(response_obj['results'][0]['id'], self.report3.id)
        self.assertEqual(response_obj['results'][1]['id'], self.report4.id)
