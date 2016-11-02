# -*- encoding: utf-8 -*-

import datetime
import json
import urllib2
from django.conf import settings

from django.core.files import File
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test.client import encode_multipart

from mock import patch
from mock import mock_open
from rest_framework.test import APITestCase

from accounts.models import UserDevice, User, Authority, UserCode
from common import factory
from common.constants import (GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA,
    GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE,  USER_STATUS_VOLUNTEER,
    USER_STATUS_PODD, USER_STATUS_LIVESTOCK, USER_STATUS_PUBLIC_HEALTH, USER_STATUS_ADDITION_VOLUNTEER)
from reports.models import Report, ReportImage, ReportComment

def mock_upload_to_s3(file):
    return 'http://2.bp.blogspot.com/-_NbC8XQ05jQ/UVly-ZzBK0I/AAAAAAAABtA/fETW0ixUnX0/s1600/image.jpg'


def mock_facebook_graph_get_object(self, id, **args):
    return {
        u'picture': {
            u'data': {
                u'url': u'https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xap1/v/t1.0-1/p200x200/1469737_693160797374375_1503926674_n.jpg?oh=3f0222140bc6e623991454b0c1010175&oe=56C75B45&__gda__=1452604903_646f4de4341bdcf0124ab82dee6f3d52',
                u'is_silhouette': False
            }
        },
        u'id': u'603719628',
        u'name': u'Taeyeon Kim',
        u'email': u'taeyeon_kim@hotmail.com'
    }


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


class TestApiLogin(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(password='password')
        self.jessica = factory.create_user()

        self.perm1 = factory.create_custom_permission()
        self.perm2 = factory.create_custom_permission()
        self.perm3 = factory.create_custom_permission()

    def test_api_get_login(self):
        response = self.client.get(reverse('obtain_auth_token'))
        self.assertEqual(response.status_code, 405)

    def test_api_post_login(self):
        params = {
            'username': self.taeyeon.username,
            'password': 'password',
        }
        response = self.client.post(reverse('obtain_auth_token'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['username'], self.taeyeon.username)
        self.assertEqual(response_json['firstName'], self.taeyeon.first_name)
        self.assertEqual(response_json['lastName'], self.taeyeon.last_name)
        self.assertEqual(response_json['status'], self.taeyeon.status)
        self.assertEqual(response_json['authorityAdmins'], [])
        self.assertEqual(response_json['isStaff'], False)
        self.assertEqual(response_json['isSuperuser'], False)
        self.assertTrue(response_json['token'])

    def test_api_post_login_invalid(self):
        params = {
            'username': self.taeyeon.username,
            'password': 'wrong',
        }
        response = self.client.post(reverse('obtain_auth_token'), params)
        self.assertEqual(response.status_code, 400)


class TestApiConfiguration(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()
        self.group_a = factory.add_user_to_new_group_type_administration_area(user=self.taeyeon)
        self.group_r = factory.add_user_to_new_group_type_report_type(user=self.taeyeon)
        self.group_a2 = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)
        self.group_r2 = factory.add_user_to_new_group(user=self.taeyeon,
            type=GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE)

        self.type1 = factory.create_report_type()
        self.type2 = factory.create_report_type()
        self.type3 = factory.create_report_type()
        factory.create_group_report_type(group=self.group_r, report_type=self.type1)
        factory.create_group_report_type(group=self.group_r2, report_type=self.type3)

        self.area1 = factory.create_administration_area()
        self.area2 = factory.create_administration_area()
        self.area3 = factory.create_administration_area()
        factory.create_group_administration_area(group=self.group_a, administration_area=self.area1)
        factory.create_group_administration_area(group=self.group_a2, administration_area=self.area1)

        factory.create_configuration(key='awsSecretKey', value='SNSD4Ever')
        factory.create_configuration(key='awsAccessKey', value='TJSpinDance')

    def test_api_configuration(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'androidId': 'NEXUS-5',
            'deviceId': 'AXcdEsddeR',
            'brand': 'Samsung',
            'model': 'Galaxy',
            'wifiMac': 'AcsdE-Bcsads',
        }
        response = self.client.post(reverse('configuration'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['fullName'], self.taeyeon.get_full_name())
        self.assertEqual(response_json['awsSecretKey'], 'SNSD4Ever')
        self.assertEqual(response_json['awsAccessKey'], 'TJSpinDance')
        self.assertEqual(len(response_json['administrationAreas']), 1)
        self.assertEqual(response_json['administrationAreas'][0]['id'], self.area1.id)
        self.assertEqual(response_json['administrationAreas'][0]['name'], self.area1.name)
        self.assertEqual(response_json['administrationAreas'][0]['address'], self.area1.address)
        self.assertEqual(response_json['administrationAreas'][0]['parentName'], self.area1.get_parent())
        self.assertEqual(response_json['administrationAreas'][0]['isLeaf'], self.area1.is_leaf())

        self.assertEqual(len(response_json['reportTypes']), 1)
        self.assertEqual(response_json['reportTypes'][0]['id'], self.type1.id)
        self.assertEqual(response_json['reportTypes'][0]['name'], self.type1.name)
        self.assertEqual(response_json['reportTypes'][0]['version'], self.type1.version)
        self.assertEqual(response_json['reportTypes'][0]['definition'], json.loads(self.type1.form_definition))

        device = UserDevice.objects.latest('id')
        self.assertEqual(device.user, self.taeyeon)
        self.assertEqual(device.android_id, 'NEXUS-5')
        self.assertEqual(device.device_id, 'AXcdEsddeR')
        self.assertEqual(device.brand, 'Samsung')
        self.assertEqual(device.model, 'Galaxy')
        self.assertEqual(device.wifi_mac, 'AcsdE-Bcsads')

    def test_api_configuration_will_return_area_including_descendants_area(self):
        area1_1 = self.area1.add_child(name='Namsan', location=self.area1.location)
        area1_1_1 = area1_1.add_child(name='Namsan Tower', location=self.area1.location)

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'androidId': 'NEXUS-5',
            'deviceId': 'AXcdEsddeR',
            'brand': 'Samsung',
            'model': 'Galaxy',
            'wifiMac': 'AcsdE-Bcsads',
        }
        response = self.client.post(reverse('configuration'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json['administrationAreas']), 3)
        self.assertEqual(response_json['administrationAreas'][0]['id'], self.area1.id)
        self.assertEqual(response_json['administrationAreas'][0]['name'], self.area1.name)
        self.assertEqual(response_json['administrationAreas'][0]['address'], self.area1.address)
        self.assertEqual(response_json['administrationAreas'][1]['id'], area1_1.id)
        self.assertEqual(response_json['administrationAreas'][1]['name'], area1_1.name)
        self.assertEqual(response_json['administrationAreas'][1]['address'], area1_1.address)
        self.assertEqual(response_json['administrationAreas'][2]['id'], area1_1_1.id)
        self.assertEqual(response_json['administrationAreas'][2]['name'], area1_1_1.name)
        self.assertEqual(response_json['administrationAreas'][2]['address'], area1_1_1.address)

    def test_api_configuration_after_have_user_device_will_update_data(self):
        self.test_api_configuration()

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'androidId': 'Xfsdefvds412xc4',
            'deviceId': 'CsaCSIbaw21ce5',
            'brand': 'LG',
            'model': 'Curve',
            'wifiMac': 'BT21:1234:2v4d:41xT',
        }
        response = self.client.post(reverse('configuration'), params)
        self.assertEqual(response.status_code, 200)

        device = UserDevice.objects.latest('id')
        self.assertEqual(device.user, self.taeyeon)
        self.assertEqual(device.android_id, 'Xfsdefvds412xc4')
        self.assertEqual(device.device_id, 'CsaCSIbaw21ce5')
        self.assertEqual(device.brand, 'LG')
        self.assertEqual(device.model, 'Curve')
        self.assertEqual(device.wifi_mac, 'BT21:1234:2v4d:41xT')

    def test_api_configuration_without_permission(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        params = {
            'androidId': 'NEXUS-5',
            'deviceId': 'AXcdEsddeR',
            'brand': 'Samsung',
            'model': 'Galaxy',
            'wifiMac': 'AcsdE-Bcsads',
        }
        response = self.client.post(reverse('configuration'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['fullName'], self.jessica.get_full_name())
        self.assertEqual(response_json['administrationAreas'], [])
        self.assertEqual(response_json['reportTypes'], [])

    def test_post_api_configuration_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.post(reverse('configuration'))
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['androidId'], ['This field is required.'])
        self.assertEqual(response_json['deviceId'], ['This field is required.'])
        self.assertEqual(response_json['brand'], ['This field is required.'])
        self.assertEqual(response_json['model'], ['This field is required.'])
        # self.assertEqual(response_json['wifiMac'], ['This field is required.'])

    def test_anonymous_cannot_access_api_configuration(self):
        response = self.client.post(reverse('configuration'))
        self.assertEqual(response.status_code, 401)


class TestApiUserSearch(APITestCase):
    def setUp(self):
        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user(username='taengu')
        self.jessica = factory.create_user(username='maomao')
        self.yoona = factory.create_user(username='maoyoong')

    def test_api_report_search(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('users_search'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 3)

        user1 = response_json[0]
        self.assertEqual(user1['id'], self.jessica.id)
        self.assertEqual(user1['username'], self.jessica.username)
        self.assertEqual(user1['firstName'], self.jessica.first_name)
        self.assertEqual(user1['lastName'], self.jessica.last_name)
        self.assertEqual(user1['fullName'], self.jessica.get_full_name())

        user2 = response_json[1]
        self.assertEqual(user2['id'], self.yoona.id)
        self.assertEqual(user2['username'], self.yoona.username)
        self.assertEqual(user2['firstName'], self.yoona.first_name)
        self.assertEqual(user2['lastName'], self.yoona.last_name)
        self.assertEqual(user2['fullName'], self.yoona.get_full_name())

        user3 = response_json[2]
        self.assertEqual(user3['id'], self.taeyeon.id)
        self.assertEqual(user3['username'], self.taeyeon.username)
        self.assertEqual(user3['firstName'], self.taeyeon.first_name)
        self.assertEqual(user3['lastName'], self.taeyeon.last_name)
        self.assertEqual(user3['fullName'], self.taeyeon.get_full_name())

    def test_api_report_search_by_username(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('users_search'), {
            'username': 'mao'
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        user1 = response_json[0]
        self.assertEqual(user1['id'], self.jessica.id)

        user2 = response_json[1]
        self.assertEqual(user2['id'], self.yoona.id)

    def test_api_report_search_by_username_case_insensitive(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('users_search'), {
            'username': 'tAEng'
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 1)

        user1 = response_json[0]
        self.assertEqual(user1['id'], self.taeyeon.id)

    def test_anonymous_cannot_access_api_list_search(self):
        response = self.client.get(reverse('users_search'))
        self.assertEqual(response.status_code, 401)


class TestApiGCMRegistration(APITestCase):
    def setUp(self):
        call_command('clear_index', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()

        self.device1 = factory.create_user_device(user=self.taeyeon)
        self.device2 = factory.create_user_device(user=self.jessica)
        self.device1.gcm_reg_id = ''
        self.device1.save()

        self.yoona = factory.create_user()

    def test_post_api_gcm_registration(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'gcmRegId': 'Akcp201',
        }
        response = self.client.post(reverse('gcm_registration'), params)
        self.assertEqual(response.status_code, 200)

        device = UserDevice.objects.get(id=self.device1.id)
        self.assertEqual(device.gcm_reg_id, 'Akcp201')

    def test_post_api_gcm_registration_already_have_gcm_reg_id_will_replace_the_old_one(self):
        self.device1.gcm_reg_id = 'SS-2904'
        self.device1.save()

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'gcmRegId': 'Akcp201',
        }
        response = self.client.post(reverse('gcm_registration'), params)
        self.assertEqual(response.status_code, 200)

        device = UserDevice.objects.get(id=self.device1.id)
        self.assertEqual(device.gcm_reg_id, 'Akcp201')

    def test_post_api_gcm_registration_with_same_gcm_reg_id_will_replace_delete_old_one(self):
        self.device1.gcm_reg_id = 'SS-2904'
        self.device1.save()

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        params = {
            'gcmRegId': 'SS-2904',
        }
        response = self.client.post(reverse('gcm_registration'), params)
        self.assertEqual(response.status_code, 200)

        device = UserDevice.objects.get(user=self.jessica)
        self.assertEqual(device.gcm_reg_id, 'SS-2904')

        with self.assertRaises(UserDevice.DoesNotExist):
            UserDevice.objects.get(user=self.taeyeon)

    def test_post_api_gcm_registration_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.post(reverse('gcm_registration'))
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['gcmRegId'], 'This field is required.')

    def test_post_api_gcm_registration_with_user_that_doesnot_have_device_will_error(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.yoona.auth_token.key)
        params = {
            'gcmRegId': 'Akcp201',
        }
        response = self.client.post(reverse('gcm_registration'), params)
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['detail'], 'This user does not register this device.')

    def test_cannot_get_api_gcm_registration(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('gcm_registration'))
        self.assertEqual(response.status_code, 405)

    def test_anonymous_cannot_access_api_gcm_registration(self):
        response = self.client.get(reverse('gcm_registration'))
        self.assertEqual(response.status_code, 401)


class TestApiProfileImageUpload(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user()
        self.jessica = factory.create_user()

        # get_temporary_file()

    @patch('accounts.api.upload_to_s3', mock_upload_to_s3)
    def test_post_profile_image_upload(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)

        m = mock_open()
        with patch('__main__.open', m, create=True):
            send_file = open('/tmp/hello.world.jpg', 'r')

        params = {
            'image': send_file,
        }

        content = encode_multipart('BoUnDaRyStRiNg', params)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

        response = self.client.post(reverse('upload_image_profile'), content, content_type=content_type)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['username'], self.taeyeon.username)
        self.assertEqual(response_json['avatarUrl'], 'http://2.bp.blogspot.com/-_NbC8XQ05jQ/UVly-ZzBK0I/AAAAAAAABtA/fETW0ixUnX0/s1600/image.jpg')
        self.assertEqual(response_json['thumbnailAvatarUrl'], 'http://2.bp.blogspot.com/-_NbC8XQ05jQ/UVly-ZzBK0I/AAAAAAAABtA/fETW0ixUnX0/s1600/image.jpg')

    def test_cannot_get_upload_profile_image(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('upload_report_image'))
        self.assertEqual(response.status_code, 405)

    def test_anonymous_cannot_post_upload_profile_image(self):
        response = self.client.post(reverse('upload_report_image'))
        self.assertEqual(response.status_code, 401)


class TestApiPing(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user()

    def test_ping_success(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('ping'))
        self.assertEqual(response.status_code, 200)

    def test_ping_with_no_token(self):
        response = self.client.get(reverse('ping'))
        self.assertEqual(response.status_code, 401)

    def test_ping_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key + '530')
        response = self.client.get(reverse('ping'))
        self.assertEqual(response.status_code, 401)


class TestApiUserProfile(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user()
        self.anonymous418 = factory.create_user(is_public=True, is_anonymous=True)
        self.anonymous309 = factory.create_user(is_public=True, is_anonymous=True)

    def test_access_user_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, 200)

    def test_cannot_access_user_profile_with_no_token(self):
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, 401)

    def test_cannot_access_user_profile_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key + '418')
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, 401)

    def test_update_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'firstName': 'Taeyeon',
            'lastName': 'Kim',
            'telephone': '6689345678',
            'avatarUrl': 'http://placehold.it/300x300',
            'thumbnailAvatarUrl': 'http://placehold.it/80x80'
        }
        response = self.client.post(reverse('user-profile'), params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.taeyeon.id)
        self.assertEqual(user.first_name, 'Taeyeon')
        self.assertEqual(user.last_name, 'Kim')
        self.assertEqual(user.telephone, '6689345678')
        self.assertEqual(user.avatar_url, 'http://placehold.it/300x300')
        self.assertEqual(user.thumbnail_avatar_url, 'http://placehold.it/80x80')

    def test_update_profile_some_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'firstName': 'Taeyeon Kim',
            'telephone': '6689345688'
        }
        response = self.client.post(reverse('user-profile'), params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.taeyeon.id)
        self.assertEqual(user.first_name, 'Taeyeon Kim')
        self.assertEqual(user.telephone, '6689345688')

    def test_update_profile_with_email(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'firstName': 'Taeyeon Kim',
            'telephone': '6689345688',
            'email': 'taeyeon_ss@gmail.com'
        }
        response = self.client.post(reverse('user-profile'), params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.taeyeon.id)
        self.assertEqual(user.first_name, 'Taeyeon Kim')
        self.assertEqual(user.telephone, '6689345688')
        self.assertEqual(user.email, 'taeyeon_ss@gmail.com')

    def test_update_is_anonymous_profile_with_email(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.anonymous418.auth_token.key)
        params = {
            'firstName': 'Jessica Jung',
            'email': 'jessica@gmail.com'
        }
        response = self.client.post(reverse('user-profile'), params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.anonymous418.id)
        self.assertEqual(user.first_name, 'Jessica Jung')
        self.assertEqual(user.email, 'jessica@gmail.com')
        self.assertFalse(user.is_anonymous)

    def test_update_is_anonymous_profile_without_email(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.anonymous418.auth_token.key)
        params = {
            'firstName': 'Jessica Jung'
        }
        response = self.client.post(reverse('user-profile'), params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.anonymous418.id)
        self.assertEqual(user.first_name, 'Jessica Jung')
        self.assertTrue(user.is_anonymous)

    @patch('facebook.GraphAPI.get_object', mock_facebook_graph_get_object)
    def test_api_user_profile_facebook_connect(self):

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.anonymous309.auth_token.key)
        params = {
            'facebook_access_token': 'CAACEdEose0cBAEPHQz2q46MV8a4m6Lg2',
        }

        response = self.client.post(reverse('user-profile'), params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.anonymous309.id)
        self.assertEqual(user.username, 'taeyeon_kim@hotmail.com')
        self.assertEqual(user.email, 'taeyeon_kim@hotmail.com')
        self.assertEqual(user.first_name, 'Taeyeon Kim')
        self.assertEqual(user.avatar_url, 'https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xap1/v/t1.0-1/p200x200/1469737_693160797374375_1503926674_n.jpg?oh=3f0222140bc6e623991454b0c1010175&oe=56C75B45&__gda__=1452604903_646f4de4341bdcf0124ab82dee6f3d52')
        self.assertEqual(user.fbuid, '603719628')
        self.assertFalse(user.is_anonymous)

    @patch('facebook.GraphAPI.get_object', mock_facebook_graph_get_object)
    def test_api_invalid_user_profile_facebook_connect_same_email(self):
        self.taeyeon_ss = factory.create_user(is_public=True, email='taeyeon_kim@hotmail.com')

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.anonymous309.auth_token.key)
        params = {
            'facebook_access_token': 'CAACEdEose0cBAEPHQz2q46MV8a4m6Lg2',
        }
        response = self.client.post(reverse('user-profile'), params)
        self.assertEqual(response.status_code, 400)

    @patch('facebook.GraphAPI.get_object', mock_facebook_graph_get_object)
    def test_api_invalid_user_profile_facebook_connect_facebook_id(self):
        self.taeyeon.fbuid = 603719628
        self.taeyeon.save()

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.anonymous309.auth_token.key)
        params = {
            'facebook_access_token': 'CAACEdEose0cBAEPHQz2q46MV8a4m6Lg2',
        }
        response = self.client.post(reverse('user-profile'), params)
        self.assertEqual(response.status_code, 400)

    @patch('facebook.GraphAPI.get_object', mock_facebook_graph_get_object)
    def test_api_user_profile_facebook_connect_again(self):
        self.anonymous309.fbuid = 603719628
        self.anonymous309.save()

        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.anonymous309.auth_token.key)
        params = {
            'facebook_access_token': 'CAACEdEose0cBAEPHQz2q46MV8a4m6Lg2',
        }
        response = self.client.post(reverse('user-profile'), params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.anonymous309.id)
        self.assertEqual(user.username, self.anonymous309.username)
        self.assertFalse(user.is_anonymous)


class TestApiUserPassword(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(status='VOLUNTEER')

    def test_post_update_user_password(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = { 'password': '1234' }
        response = self.client.post(reverse('user_update_password'), params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.taeyeon.id)
        self.assertEqual(user.display_password, '1234')

    def test_post_update_user_password_with_zero(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = { 'password': '01234' }
        response = self.client.post(reverse('user_update_password'), params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.taeyeon.id)
        self.assertEqual(user.display_password, '01234')

    def test_post_update_user_password_with_len_less_than_4(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = { 'password': '123' }
        response = self.client.post(reverse('user_update_password'), params)
        response_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json['password'], 'Invalid password. Please try again. Only Number[0-9] and length > 3 (eg. 1234)')

    def test_post_update_user_password_with_wrong_type(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = { 'password': 'abcdef' }
        response = self.client.post(reverse('user_update_password'), params)
        response_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json['password'], 'Invalid password. Please try again. Only Number[0-9] and length > 3 (eg. 1234)')

    def test_post_update_user_password_with_no_input(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.post(reverse('user_update_password'))
        response_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json['password'], 'Invalid password. Please try again. Only Number[0-9] and length > 3 (eg. 1234)')

    def test_cannot_access_user_password(self):
        params = { 'password': '1234' }
        response = self.client.post(reverse('user_update_password'), params)
        self.assertEqual(response.status_code, 401)


class TestApiConfiguration(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(is_staff=True)
        self.jessica = factory.create_user()

        factory.create_configuration(system='snsd', key='kim', value='taeyeon')
        factory.create_configuration(system='sms', key='username', value='koyoyo')
        factory.create_configuration(system='sms', key='password', value='pass')

    def test_get_list_configurations(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'system': 'sms'
        }
        response = self.client.get(reverse('list_configuration'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['username'], 'koyoyo')
        self.assertEqual(response_json['password'], 'pass')

    def test_get_list_configurations_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('list_configuration'))
        self.assertEqual(response.status_code, 400)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['system'], 'System is required.')

    def test_not_staff_user_cannot_access_api_configuration(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.get(reverse('list_configuration'))
        self.assertEqual(response.status_code, 401)

    def test_anonymous_cannot_access_api_configuration(self):
        response = self.client.get(reverse('list_configuration'))
        self.assertEqual(response.status_code, 401)


class TestApiRegistrationByAutority(APITestCase):
    def setUp(self):
        call_command('log_action_create', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user(telephone="0841299999")
        self.jessica = factory.create_user()

        self.authority = factory.create_authority()
        self.invitation_code = self.authority.get_invite().code

    def test_get_autority_by_no_invitation_code(self):
        response = self.client.get(reverse('get_authority_by_invitation_code'))
        self.assertEqual(response.status_code, 400)

    def test_get_autority_by_wrong_invitation_code(self):
        params = { 'invitationCode': 'AA-1123' }
        response = self.client.get(reverse('get_authority_by_invitation_code'), params)
        self.assertEqual(response.status_code, 400)

    def test_get_authority_by_invitation_code(self):
        params = { 'invitationCode': self.invitation_code }
        response = self.client.get(reverse('get_authority_by_invitation_code'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['code'], self.authority.code)
        self.assertEqual(response_json['name'], self.authority.name)

    def test_registration_user(self):
        params = {
            'firstName': 'yoona',
            'lastName': 'im',
            'serialNumber': '0000000000530',
            'telephone': '0800000530',
            'authority': self.invitation_code
        }
        response = self.client.post(reverse('user_register_by_authority'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['firstName'], 'yoona')
        self.assertEqual(response_json['lastName'], 'im')
        self.assertEqual(response_json['status'], USER_STATUS_ADDITION_VOLUNTEER)

        user = User.objects.latest('id')
        self.assertEqual(user.first_name, 'yoona')
        self.assertEqual(user.last_name, 'im')
        self.assertEqual(user.status, USER_STATUS_ADDITION_VOLUNTEER)

        authority = Authority.objects.get(id=self.authority.id)
        self.assertEqual(authority.users.count(), 1)

        user_authority1 = authority.users.all()[0]
        self.assertEqual(user_authority1.first_name, 'yoona')
        self.assertEqual(user_authority1.last_name, 'im')

    def test_registration_user_with_status(self):
        params = {
            'firstName': 'yoona',
            'lastName': 'im',
            'serialNumber': '0000000000530',
            'telephone': '0800000530',
            'authority': self.invitation_code,
            'status': USER_STATUS_PODD
        }
        response = self.client.post(reverse('user_register_by_authority'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['firstName'], 'yoona')
        self.assertEqual(response_json['lastName'], 'im')
        self.assertEqual(response_json['status'], USER_STATUS_PODD)

        user = User.objects.latest('id')
        self.assertEqual(user.first_name, 'yoona')
        self.assertEqual(user.last_name, 'im')
        self.assertEqual(user.status, USER_STATUS_PODD)

        authority = Authority.objects.get(id=self.authority.id)
        self.assertEqual(authority.users.count(), 1)

        user_authority1 = authority.users.all()[0]
        self.assertEqual(user_authority1.first_name, 'yoona')
        self.assertEqual(user_authority1.last_name, 'im')

    def test_registration_user_with_no_authority(self):
        params = {
            'firstName': 'yoona',
            'lastName': 'im',
            'serialNumber': '0000000000530',
            'telephone': '0800000530',
        }
        response = self.client.post(reverse('user_register_by_authority'), params)
        self.assertEqual(response.status_code, 400)

    def test_registration_user_with_same_serial_number(self):
        params = {
            'firstName': 'krystal',
            'lastName': 'jung',
            'serialNumber': self.taeyeon.serial_number,
            'telephone': '0800000530',
        }
        response = self.client.post(reverse('user_register_by_authority'), params)
        self.assertEqual(response.status_code, 400)

    def test_registration_user_with_same_telephone(self):
        params = {
            'firstName': 'krystal',
            'lastName': 'jung',
            'serialNumber': '1411900088888',
            'telephone': '0841299999',
        }
        response = self.client.post(reverse('user_register_by_authority'), params)
        self.assertEqual(response.status_code, 400)

'''
class TestApiRegistrationByGroup(APITestCase):
    def setUp(self):
        call_command('log_action_create', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user(telephone="0841299999")
        self.jessica = factory.create_user()

        self.invite_group = factory.create_invite_group()
        self.group_r = factory.create_group_type_report_type()
        self.group_a = factory.create_group_type_report_type()

        self.invite_group.groups.add(self.group_r)
        self.invite_group.groups.add(self.group_a)

        self.invitation_code = self.invite_group.code

    def test_get_autority_by_no_invitation_code(self):
        response = self.client.get(reverse('get_group_by_invitation_code'))
        self.assertEqual(response.status_code, 400)

    def test_get_autority_by_wrong_invitation_code(self):
        params = { 'invitationCode': '21123' }
        response = self.client.get(reverse('get_group_by_invitation_code'), params)
        self.assertEqual(response.status_code, 400)

    def test_get_authority_by_invitation_code(self):
        params = { 'invitationCode': self.invitation_code }
        response = self.client.get(reverse('get_group_by_invitation_code'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['name'], self.invite_group.name)

    def test_registration_user(self):
        params = {
            'firstName': 'yoona',
            'lastName': 'im',
            'serialNumber': '0000000000530',
            'telephone': '0800000530',
            'group': self.invitation_code
        }
        response = self.client.post(reverse('user_register_by_group'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['firstName'], 'yoona')
        self.assertEqual(response_json['lastName'], 'im')
        self.assertEqual(response_json['status'], USER_STATUS_ADDITION_VOLUNTEER)

        user = User.objects.latest('id')
        self.assertEqual(user.first_name, 'yoona')
        self.assertEqual(user.last_name, 'im')
        self.assertEqual(user.status, USER_STATUS_ADDITION_VOLUNTEER)
        self.assertEqual(user.groups.count(), 2)

    def test_registration_user_with_status(self):
        params = {
            'firstName': 'yoona',
            'lastName': 'im',
            'serialNumber': '0000000000530',
            'telephone': '0800000530',
            'group': self.invitation_code,
            'status': USER_STATUS_PODD
        }
        response = self.client.post(reverse('user_register_by_group'), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['firstName'], 'yoona')
        self.assertEqual(response_json['lastName'], 'im')
        self.assertEqual(response_json['status'], USER_STATUS_PODD)

        user = User.objects.latest('id')
        self.assertEqual(user.first_name, 'yoona')
        self.assertEqual(user.last_name, 'im')
        self.assertEqual(user.status, USER_STATUS_PODD)
        self.assertEqual(user.groups.count(), 2)

    def test_registration_user_with_no_authority(self):
        params = {
            'firstName': 'yoona',
            'lastName': 'im',
            'serialNumber': '0000000000530',
            'telephone': '0800000530',
        }
        response = self.client.post(reverse('user_register_by_group'), params)
        self.assertEqual(response.status_code, 400)

    def test_registration_user_with_same_serial_number(self):
        params = {
            'firstName': 'krystal',
            'lastName': 'jung',
            'serialNumber': self.taeyeon.serial_number,
            'telephone': '0800000530',
        }
        response = self.client.post(reverse('user_register_by_group'), params)
        self.assertEqual(response.status_code, 400)

    def test_registration_user_with_same_telephone(self):
        params = {
            'firstName': 'krystal',
            'lastName': 'jung',
            'serialNumber': '1411900088888',
            'telephone': '0841299999',
        }
        response = self.client.post(reverse('user_register_by_group'), params)
        self.assertEqual(response.status_code, 400)
'''

class TestApiForgotPassword(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(serial_number='0000000000309')

    def test_post_forgot_password_no_serial_number_and_no_email(self):
        response = self.client.post(reverse('user_forgot_password'))
        self.assertEqual(response.status_code, 400)

    def test_post_forgot_password_wrong_serial_number(self):
        params = {
            'serialNumber': '0000000000530'
        }
        response = self.client.post(reverse('user_forgot_password'), params)
        self.assertEqual(response.status_code, 400)

    def test_post_forgot_password_wrong_email(self):
        params = {
            'email': '12345678@gmail.com'
        }
        response = self.client.post(reverse('user_forgot_password'), params)
        self.assertEqual(response.status_code, 400)

    def test_post_forgot_password_serial_number(self):
        params = {
            'serialNumber': self.taeyeon.serial_number
        }
        response = self.client.post(reverse('user_forgot_password'), params)
        self.assertEqual(response.status_code, 200)

    def test_post_forgot_password_email(self):
        params = {
            'email': self.taeyeon.email
        }
        response = self.client.post(reverse('user_forgot_password'), params)
        self.assertEqual(response.status_code, 200)


class TestApiLoginWithCode(APITestCase):
    def setUp(self):
        call_command('log_action_create', interactive=False, verbosity=0)

        self.taeyeon = factory.create_user(serial_number='0000000000309')
        self.jessica = factory.create_user(serial_number='0000000000418')

        self.code1 = factory.create_user_code(user=self.jessica)

    def test_post_forgot_password_no_serial_number(self):
        response = self.client.post(reverse('user_forgot_password'))
        self.assertEqual(response.status_code, 400)

    def test_post_forgot_password_wrong_serial_number(self):
        params = { 'serialNumber': '0000000000530' }
        response = self.client.post(reverse('user_forgot_password'), params)
        self.assertEqual(response.status_code, 400)

    def test_post_forgot_password_serial_number(self):
        params = { 'serialNumber': self.taeyeon.serial_number }
        response = self.client.post(reverse('user_forgot_password'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertIsNotNone(response_json['uid'])
        self.assertIsNotNone(response_json['token'])

        uid = response_json['uid']
        token = response_json['token']
        user_code = UserCode.objects.latest('id')

        params = { 'code': user_code.code }
        response = self.client.post(reverse('user_code_login', args=[uid, token]), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['firstName'], self.taeyeon.first_name)
        self.assertEqual(response_json['lastName'], self.taeyeon.last_name)

    def test_post_forgot_password_serial_number_wrong_user_code(self):
        params = { 'serialNumber': self.taeyeon.serial_number }
        response = self.client.post(reverse('user_forgot_password'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertIsNotNone(response_json['uid'])
        self.assertIsNotNone(response_json['token'])

        uid = response_json['uid']
        token = response_json['token']

        params = { 'code': self.code1.code }
        response = self.client.post(reverse('user_code_login', args=[uid, token]), params)
        self.assertEqual(response.status_code, 400)

    def test_post_forgot_password_serial_number_used_user_code(self):
        params = { 'serialNumber': self.taeyeon.serial_number }
        response = self.client.post(reverse('user_forgot_password'), params)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertIsNotNone(response_json['uid'])
        self.assertIsNotNone(response_json['token'])

        uid = response_json['uid']
        token = response_json['token']
        user_code = UserCode.objects.latest('id')

        params = { 'code': user_code.code }
        response = self.client.post(reverse('user_code_login', args=[uid, token]), params)
        self.assertEqual(response.status_code, 200)

        params = { 'code': user_code.code }
        response = self.client.post(reverse('user_code_login', args=[uid, token]), params)
        self.assertEqual(response.status_code, 400)


class TestApiAuthority(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(is_staff=True)
        self.jessica = factory.create_user()

        self.authority1 = factory.create_authority()
        self.authority1_1 = factory.create_authority()

        self.authority1_1.parent = self.authority1
        self.authority1_1.save()

    def test_get_list_authority(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        response = self.client.get(reverse('authority-list'))
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content)
        self.assertEqual(len(response_json), 2)

        authority1 = response_json[0]
        self.assertEqual(authority1['id'], self.authority1.id)
        # self.assertEqual(authority1['parent'], None)

        authority2 = response_json[1]
        self.assertEqual(authority2['id'], self.authority1_1.id)
        # self.assertEqual(authority2['parent'], self.authority1.id)

    # def test_get_list_authority_filter_parent(self):
    #     self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
    #     params = {
    #         'parentId': self.authority1.id,
    #     }
    #     response = self.client.get(reverse('authority-list'), params)
    #     self.assertEqual(response.status_code, 200)

    #     response_json = json.loads(response.content)
    #     self.assertEqual(len(response_json), 1)

    #     authority1 = response_json[0]
    #     self.assertEqual(authority1['id'], self.authority1_1.id)
    #     self.assertEqual(authority1['parent'], self.authority1.id)

    # def test_get_list_authority_filter_none_parent(self):
    #     self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
    #     params = {
    #         'parentId': None,
    #     }
    #     response = self.client.get(reverse('authority-list'), params)
    #     self.assertEqual(response.status_code, 200)

    #     response_json = json.loads(response.content)
    #     self.assertEqual(len(response_json), 1)

    #     authority1 = response_json[0]
    #     self.assertEqual(authority1['id'], self.authority1.id)
    #     self.assertEqual(authority1['parent'], None)

    def test_api_delete_authority_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.jessica.auth_token.key)
        response = self.client.delete(reverse('authority-detail', args=[self.authority1.id]))
        self.assertEqual(response.status_code, 403)


class TestApiRegistrationByUserDevice(APITestCase):
    def setUp(self):
        call_command('log_action_create', interactive=False, verbosity=0)
        self.domain_id = settings.CURRENT_DOMAIN_ID
        self.authority = Authority.objects.create(code='public_%s' % settings.CURRENT_DOMAIN_ID,
                                                  name='public_%s' % settings.CURRENT_DOMAIN_ID)

    def test_registration_user_by_gcm_reg_id(self):
        params = {
            'deviceId': '123456789',
            'brand': 'im-mobile',
            'model': 'im4',
            'gcmRegId': 'FA91bEWLspNo7KZaBjJjMZAHaRPpl3HMOrNAq995twkB2v3t_'
        }
        response = self.client.post(reverse('user_register_by_user_device', args=[self.domain_id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertTrue('Anonymous' in response_json['username'])
        self.assertEqual(response_json['status'], USER_STATUS_ADDITION_VOLUNTEER)

        user = User.objects.latest('id')
        self.assertTrue('Anonymous' in user.username)
        self.assertEqual(user.status, USER_STATUS_ADDITION_VOLUNTEER)
        self.assertTrue(user.is_anonymous)
        self.assertTrue(user.is_public)

        device = UserDevice.objects.latest('id')
        self.assertEqual(device.device_id, '123456789')
        self.assertEqual(device.brand, 'im-mobile')
        self.assertEqual(device.model, 'im4')
        self.assertEqual(device.gcm_reg_id, 'FA91bEWLspNo7KZaBjJjMZAHaRPpl3HMOrNAq995twkB2v3t_')

        authority = Authority.objects.get(code='public_%s' % settings.CURRENT_DOMAIN_ID)
        self.assertEqual(authority.name, 'public_%s' % settings.CURRENT_DOMAIN_ID)
        self.assertEqual(authority.users.filter(id=user.id).count(), 1)

    def test_registration_user_by_apns_reg_id(self):
        params = {
            'deviceId': '987654321',
            'brand': 'iphone',
            'model': 'iphone4',
            'apnsRegId': 'e38ee577fd3e0dd2'
        }
        response = self.client.post(reverse('user_register_by_user_device', args=[self.domain_id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertTrue('Anonymous' in response_json['username'])
        self.assertEqual(response_json['status'], USER_STATUS_ADDITION_VOLUNTEER)

        user = User.objects.latest('id')
        self.assertTrue('Anonymous' in user.username)
        self.assertEqual(user.status, USER_STATUS_ADDITION_VOLUNTEER)
        self.assertTrue(user.is_anonymous)
        self.assertTrue(user.is_public)

        device = UserDevice.objects.latest('id')
        self.assertEqual(device.device_id, '987654321')
        self.assertEqual(device.brand, 'iphone')
        self.assertEqual(device.model, 'iphone4')
        self.assertEqual(device.apns_reg_id, 'e38ee577fd3e0dd2')

        authority = Authority.objects.get(code='public_%s' % settings.CURRENT_DOMAIN_ID)
        self.assertEqual(authority.name, 'public_%s' % settings.CURRENT_DOMAIN_ID)
        self.assertEqual(authority.users.filter(id=user.id).count(), 1)

    def test_registration_user_with_no_gcm_reg_id_and_no_apns_id(self):
        params = {
            'deviceId': '987654321',
            'brand': 'iphone',
            'model': 'iphone4',
        }
        response = self.client.post(reverse('user_register_by_user_device', args=[self.domain_id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertTrue('Anonymous' in response_json['username'])
        self.assertEqual(response_json['status'], USER_STATUS_ADDITION_VOLUNTEER)

        user = User.objects.latest('id')
        self.assertTrue('Anonymous' in user.username)
        self.assertEqual(user.status, USER_STATUS_ADDITION_VOLUNTEER)
        self.assertTrue(user.is_anonymous)
        self.assertTrue(user.is_public)

        device = UserDevice.objects.latest('id')
        self.assertEqual(device.device_id, '987654321')
        self.assertEqual(device.brand, 'iphone')
        self.assertEqual(device.model, 'iphone4')

    def test_registration_user_same_device(self):
        params = {
            'deviceId': '987654321',
            'brand': 'iphone',
            'model': 'iphone4',
        }
        response = self.client.post(reverse('user_register_by_user_device', args=[self.domain_id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertTrue('Anonymous' in response_json['username'])
        self.assertEqual(response_json['status'], USER_STATUS_ADDITION_VOLUNTEER)

        id = response_json['id']
        username = response_json['username']

        response = self.client.post(reverse('user_register_by_user_device', args=[self.domain_id]), params)
        self.assertEqual(response.status_code, 201)

        user = User.objects.latest('id')
        self.assertEqual(user.id, id)
        self.assertEqual(user.username, username)

        device = UserDevice.objects.latest('id')
        self.assertEqual(device.device_id, '987654321')
        self.assertEqual(device.brand, 'iphone')
        self.assertEqual(device.model, 'iphone4')

    def test_registration_user_with_gcm_reg_id_and_apns_id(self):
        params = {
            'deviceId': '987654321',
            'brand': 'iphone',
            'model': 'iphone4',
            'gcmRegId': 'FA91bEWLspNo7KZaBjJjMZAHaRPpl3HMOrNAq995twkB2v3t_',
            'apnsRegId': 'e38ee577fd3e0dd2'
        }
        response = self.client.post(reverse('user_register_by_user_device', args=[self.domain_id]), params)
        self.assertEqual(response.status_code, 400)

'''
class TestApiRegistrationByFacebook(APITestCase):
    def setUp(self):
        call_command('log_action_create', interactive=False, verbosity=0)
        self.domain_id = 1

    @patch('facebook.GraphAPI.get_object', mock_facebook_graph_get_object)
    @patch('accounts.api.upload_to_s3', mock_upload_to_s3)
    def test_api_facebook_connect(self):
        params = {
            'facebook_access_token': 'CAACEdEose0cBAEPHQz2q46MV8a4m6Lg2',
        }
        response = self.client.post(reverse('facebook_connect', args=[self.domain_id]), params)
        self.assertEqual(response.status_code, 201)

        response_json = json.loads(response.content)
        self.assertEqual(response_json['email'], 'taeyeon_kim@hotmail.com')
        self.assertEqual(response_json['firstName'], 'Taeyeon Kim')
        self.assertEqual(response_json['avatarUrl'], 'https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xap1/v/t1.0-1/p200x200/1469737_693160797374375_1503926674_n.jpg?oh=3f0222140bc6e623991454b0c1010175&oe=56C75B45&__gda__=1452604903_646f4de4341bdcf0124ab82dee6f3d52')
        self.assertFalse(response_json['isAnonymous'])

        user = User.objects.latest('id')
        self.assertEqual(user.username, 'taeyeon_kim@hotmail.com')
        self.assertEqual(user.email, 'taeyeon_kim@hotmail.com')
        self.assertEqual(user.first_name, 'Taeyeon Kim')
        self.assertEqual(user.avatar_url, 'https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xap1/v/t1.0-1/p200x200/1469737_693160797374375_1503926674_n.jpg?oh=3f0222140bc6e623991454b0c1010175&oe=56C75B45&__gda__=1452604903_646f4de4341bdcf0124ab82dee6f3d52')
        self.assertEqual(user.fbuid, '603719628')
        self.assertFalse(user.is_anonymous)
        self.assertTrue(user.is_public)

        authority = Authority.objects.get(code='public_1')
        self.assertEqual(authority.name, 'public_1')
        self.assertEqual(authority.users.filter(id=user.id).count(), 1)

'''


class TestApiUserDevice(APITestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(status='VOLUNTEER')
        self.jessica = factory.create_user(status='VOLUNTEER')
        self.anonymous530 = factory.create_user(is_public=True, is_anonymous=True)

        self.device1 = factory.create_user_device(user=self.jessica)
        self.device2 = factory.create_user_device(user=self.anonymous530)

    def test_post_update_user_device(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'deviceId': '987654321',
            'brand': 'iphone',
            'model': 'iphone4',
        }
        response = self.client.post(reverse('user_update_device'), params)
        self.assertEqual(response.status_code, 200)

        device = UserDevice.objects.get(device_id='987654321')
        self.assertEqual(device.device_id, '987654321')
        self.assertEqual(device.brand, 'iphone')
        self.assertEqual(device.model, 'iphone4')
        self.assertEqual(device.user, self.taeyeon)

    def test_post_update_user_device_with_gcm_reg_id(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'deviceId': '123456789',
            'brand': 'im-mobile',
            'model': 'im4',
            'gcmRegId': 'FA91bEWLspNo7KZaBjJjMZAHaRPpl3HMOrNAq995twkB2v3t_'
        }
        response = self.client.post(reverse('user_update_device'), params)
        self.assertEqual(response.status_code, 200)

        device = UserDevice.objects.get(device_id='123456789')
        self.assertEqual(device.device_id, '123456789')
        self.assertEqual(device.brand, 'im-mobile')
        self.assertEqual(device.model, 'im4')
        self.assertEqual(device.gcm_reg_id, 'FA91bEWLspNo7KZaBjJjMZAHaRPpl3HMOrNAq995twkB2v3t_')
        self.assertEqual(device.user, self.taeyeon)

    def test_post_update_user_device_with_apns_reg_id(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'deviceId': '987654321',
            'brand': 'iphone',
            'model': 'iphone4',
            'apnsRegId': 'e38ee577fd3e0dd2'
        }
        response = self.client.post(reverse('user_update_device'), params)
        self.assertEqual(response.status_code, 200)

        device = UserDevice.objects.get(device_id='987654321')
        self.assertEqual(device.device_id, '987654321')
        self.assertEqual(device.brand, 'iphone')
        self.assertEqual(device.model, 'iphone4')
        self.assertEqual(device.apns_reg_id, 'e38ee577fd3e0dd2')
        self.assertEqual(device.user, self.taeyeon)

    def test_post_update_user_device_with_gcm_reg_id_and_apns_reg_id(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'deviceId': '987654321',
            'brand': 'iphone',
            'model': 'iphone4',
            'gcmRegId': 'FA91bEWLspNo7KZaBjJjMZAHaRPpl3HMOrNAq995twkB2v3t_',
            'apnsRegId': 'e38ee577fd3e0dd2'
        }
        response = self.client.post(reverse('user_update_device'), params)
        self.assertEqual(response.status_code, 400)

    def test_post_update_same_user_device(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'deviceId': self.device1.device_id,
            'brand': 'iphone',
            'model': 'iphone4',
        }
        response = self.client.post(reverse('user_update_device'), params)
        self.assertEqual(response.status_code, 200)

        device = UserDevice.objects.get(device_id=self.device1.device_id)
        self.assertEqual(device.device_id, self.device1.device_id)
        self.assertEqual(device.brand, 'iphone')
        self.assertEqual(device.model, 'iphone4')
        self.assertEqual(device.user, self.taeyeon)

    def test_post_update_same_anonymous_user_device(self):
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.taeyeon.auth_token.key)
        params = {
            'deviceId': self.device2.device_id,
            'brand': 'iphone',
            'model': 'iphone4',
        }
        response = self.client.post(reverse('user_update_device'), params)
        self.assertEqual(response.status_code, 200)

        device = UserDevice.objects.get(device_id=self.device2.device_id)
        self.assertEqual(device.device_id, self.device2.device_id)
        self.assertEqual(device.brand, 'iphone')
        self.assertEqual(device.model, 'iphone4')
        self.assertEqual(device.user, self.taeyeon)

        user = User.objects.get(id=self.anonymous530.id)
        self.assertFalse(user.is_active)

    def test_cannot_access_user_update_device(self):
        params = {
            'deviceId': '987654321',
            'brand': 'iphone',
            'model': 'iphone4',
        }
        response = self.client.post(reverse('user_update_device'), params)
        self.assertEqual(response.status_code, 401)
