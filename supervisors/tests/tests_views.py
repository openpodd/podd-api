# -*- encoding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.test import TestCase

from accounts.models import User
from common import factory
from common.constants import GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA, USER_STATUS_VOLUNTEER


class TestSupervisorsUserlist(TestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(is_superuser=True, status=USER_STATUS_VOLUNTEER)
        self.jessica = factory.create_user(status=USER_STATUS_VOLUNTEER)
        self.yoona = factory.create_user(status=USER_STATUS_VOLUNTEER)
        self.minah = factory.create_user(status=USER_STATUS_VOLUNTEER)

        self.area1 = factory.create_administration_area(name='Seoul')
        self.area1_1 = factory.add_child_administration_area(name='Namsan', area=self.area1)
        self.area1_2 = factory.add_child_administration_area(name='Mapo', area=self.area1)
        self.area2 = factory.create_administration_area(name='Busan')

        # ADD USER TO GROUP
        self.group1 = factory.create_group_type_administration_area()
        self.taeyeon.groups.add(self.group1)
        self.jessica.groups.add(self.group1)

        self.group2 = factory.create_group(type=GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA)
        self.minah.groups.add(self.group2)

        self.group3 = factory.create_group_type_report_type()
        self.yoona.groups.add(self.group3)

        factory.create_group_administration_area(group=self.group1, administration_area=self.area1)
        factory.create_group_administration_area(group=self.group2, administration_area=self.area1)
        factory.create_group_administration_area(group=self.group3, administration_area=self.area1)

    def test_access_supervisors_users(self):
        self.client.login(username=self.taeyeon.username, password='password')
        response = self.client.get(reverse('supervisors_users_by_status', args=['volunteer']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'supervisors/supervisors_users_list.html')
        self.client.logout()

    def test_anonymous_cannot_access_supervisors_users(self):
        response = self.client.get(reverse('supervisors_users'))
        self.assertRedirects(response, '%s?next=%s' % (reverse('accounts_login'), reverse('supervisors_users')))

    def test_not_superuser_cannot_access_supervisors_users(self):
        self.client.login(username=self.jessica.username, password='password')
        response = self.client.get(reverse('supervisors_users'))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

    def test_supervisors_users(self):
        self.client.login(username=self.taeyeon.username, password='password')
        response = self.client.get(reverse('supervisors_users_by_status', args=['volunteer']))
        self.assertEqual(response.context['areas'].count(), 2)
        self.assertEqual(response.context['areas'][0], self.area2)
        self.assertEqual(response.context['areas'][0].get_children().count(), 0)
        self.assertEqual(response.context['areas'][1], self.area1)
        self.assertIn(self.area1_1, response.context['areas'][1].get_children())
        self.assertIn(self.area1_2, response.context['areas'][1].get_children())

        self.assertContains(response, self.area1.name, 3) # Namelist 1 + User Area 2
        self.assertContains(response, self.area2.name, 1)
        self.assertContains(response, self.area1_1.name, 1)
        self.assertContains(response, self.area1_2.name, 1)

        self.assertContains(response, self.taeyeon.get_full_name(), 2) # Namelist 1 + Group Area 1
        self.assertContains(response, self.jessica.get_full_name(), 2) # Namelist 1 + Group Area 1
        self.assertContains(response, self.yoona.get_full_name(), 1) # Namelist 1
        self.assertContains(response, self.minah.get_full_name(), 1) # Namelist 1

        self.client.logout()


class TestSupervisorsUserEdit(TestCase):
    def setUp(self):
        self.taeyeon = factory.create_user(is_superuser=True)
        self.jessica = factory.create_user(status=USER_STATUS_VOLUNTEER)

    def test_access_supervisors_user_edit(self):
        self.client.login(username=self.taeyeon.username, password='password')
        response = self.client.get(reverse('supervisors_users_edit', args=[self.jessica.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'supervisors/supervisors_users_form.html')
        self.client.logout()

    def test_anonymous_cannot_access_supervisors_user_edit(self):
        response = self.client.get(reverse('supervisors_users_edit', args=[self.jessica.id]))
        self.assertRedirects(response, '%s?next=%s' % (reverse('accounts_login'), reverse('supervisors_users_edit', args=[self.jessica.id])))

    def test_not_superuser_cannot_access_supervisors_user_edit(self):
        self.client.login(username=self.jessica.username, password='password')
        response = self.client.get(reverse('supervisors_users_edit', args=[self.jessica.id]))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

    def test_post_superusers_user_edit(self):
        self.client.login(username=self.taeyeon.username, password='password')
        params = {
            'first_name': 'Jessica',
            'last_name': 'Jung',
            'email': 'sy.jessica@kmail.com',
            'contact': '333/29 Chiang Mai, Thailand',
            'telephone': '087-1801422',
            'project_mobile_number': '087-1801423',
            'serial_number': 'ASdmC2DO0x#',
            'running_number': 'S-002',
            'note': 'This is NOTE2',
            'status': USER_STATUS_VOLUNTEER,
        }
        response = self.client.post(reverse('supervisors_users_edit', args=[self.jessica.id]), params)
        self.assertEqual(response.status_code, 200)

        jessica = User.objects.get(id=self.jessica.id)
        self.assertEqual(jessica.first_name, 'Jessica')
        self.assertEqual(jessica.last_name, 'Jung')
        self.assertEqual(jessica.email, 'sy.jessica@kmail.com')
        self.assertEqual(jessica.contact, '333/29 Chiang Mai, Thailand')
        self.assertEqual(jessica.telephone, '087-1801422')
        self.assertEqual(jessica.project_mobile_number, '087-1801423')
        self.assertEqual(jessica.serial_number, 'ASdmC2DO0x#')
        self.assertEqual(jessica.running_number, 'S-002')
        self.assertEqual(jessica.note, 'This is NOTE2')
        self.assertEqual(jessica.status, USER_STATUS_VOLUNTEER)

        self.client.logout()

    def test_post_superusers_user_edit_invalid(self):
        self.client.login(username=self.taeyeon.username, password='password')
        params = {
            'first_name': '',
            'last_name': '',
        }
        response = self.client.post(reverse('supervisors_users_edit', args=[self.jessica.id]), params)
        self.assertFormError(response, 'form', 'first_name', 'This field is required.')
        self.assertFormError(response, 'form', 'last_name', 'This field is required.')

