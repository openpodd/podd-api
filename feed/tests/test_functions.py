import datetime

from django.conf import settings
from django.test import TestCase
from django_redis import get_redis_connection
from mock import patch
from mockredis import mock_strict_redis_client

from common import factory
from feed.functions import get_public_feed_key, warm_cache_public_feed, purge_all_expired_cache
from feed.tests.test_api import feedSetUp


@patch('django_redis.get_redis_connection', mock_strict_redis_client)
class TestFunctions(TestCase):
    def setUp(self):
        feedSetUp(self)

    def test_get_public_feed_key(self):
        administration_area = factory.create_administration_area()
        key = get_public_feed_key(administration_area)
        self.assertIsNotNone(key)

    def test_warm_cache_public_feed(self):
        redis = get_redis_connection()
        ''':type redis: redis.StrictRedis'''
        redis.flushall()

        feed_key = get_public_feed_key(self.public_admin_area)
        self.assertEqual(redis.zcard(feed_key), 0)

        warm_cache_public_feed()
        self.assertEqual(redis.zcard(feed_key), 4)

    def test_purge_expired_cache(self):
        redis = get_redis_connection()
        ''':type redis: redis.StrictRedis'''
        redis.flushall()
        warm_cache_public_feed()
        self.report4.created_at = datetime.datetime.now() - datetime.timedelta(days=35)
        self.report4.save()

        self.assertEqual(redis.zcard(self.report4.get_public_feed_key()), 4)

        setattr(settings, 'FEED_CACHE_PERIOD_LIMIT', datetime.timedelta(days=30))
        purge_all_expired_cache()

        self.assertEqual(redis.zcard(self.report4.get_public_feed_key()), 3)

