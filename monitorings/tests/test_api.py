# -*- encoding: utf-8 -*-
import json
import urllib2

from django.core.files import File
from django.core.urlresolvers import reverse
from django.test.client import encode_multipart

from mock import patch
from mock import mock_open

from rest_framework.test import APITestCase

from common import factory

from monitorings.models import Monitoring


def get_temporary_file():
    m = mock_open()
    with patch('__main__.open', m, create=True):
        temporary_file = open('/tmp/hello.world', 'w')
        file = File(temporary_file)
        file.write(urllib2.urlopen('http://2.bp.blogspot.com/-_NbC8XQ05jQ/UVly-ZzBK0I/AAAAAAAABtA/fETW0ixUnX0/s1600/image.jpg').read())
        file.closed
        temporary_file.closed
    return temporary_file


class TestApiMonitoringList(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(is_staff=True)
        self.jessica = factory.create_user()

        get_temporary_file()
        
    def test_get_api_monitoring_list_with_user_can_access(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('monitoring-list'))
        self.assertEqual(response.status_code, 200)

    def test_get_api_monitoring_list_with_user_can_not_access(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('monitoring-list'))
        self.assertEqual(response.status_code, 403)

    def test_post_api_monitoring_list(self):
        m = mock_open()
        with patch('__main__.open', m, create=True):
            send_file = open('/tmp/hello.world', 'r')
        params = {
            "uploadedfile": send_file,
        }
        content = encode_multipart('BoUnDaRyStRiNg', params)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

        response = self.client.post(reverse('monitoring-upload'), content, content_type=content_type)
        send_file.closed
        self.assertEqual(response.status_code, 200)


