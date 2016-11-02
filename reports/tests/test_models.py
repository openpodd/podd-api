# -*- encoding: utf-8 -*-
import json
import datetime
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core import mail

from django.test import TestCase
from django.utils import timezone
from django_redis import get_redis_connection
from freezegun import freeze_time
import mock
from mockredis import mock_strict_redis_client

from accounts.models import Authority, User
from common import factory
from common.constants import NEWS_TYPE_SUBSCRIBE_AUTHORITY, USER_STATUS_ADDITION_VOLUNTEER
from common.factory import randnum, randstr
from feed.functions import get_public_feed_key
from notifications.models import NotificationTemplate, NotificationAuthority, Notification, FollowUp
from notifications.tasks import send_alert_follow_up
from reports.models import (
    CaseDefinition, ReportState, Report, ReportType,
    ReportComment, AdministrationArea, ReportLike, ReportMeToo
)
from django.test import Client


@mock.patch('django_redis.get_redis_connection', mock_strict_redis_client)
class TestSafety(TestCase):

    def setUp(self):
        self.report_type = factory.create_report_type(name='TestCaseDefinition', code='TestCaseDefinition', form_definition={
            "startPageId": 1,
            "questions": [
                {
                    "id": 1,
                    "name": "animalType",
                    "title": u"ประเภทสัตว์",
                    "type": "single",
                    "items": [
                        { "id": u"สัตว์ปีก", "text": u"สัตว์ปีก" },
                        { "id": u"สัตว์กระเพาะเดี่ยว", "text": u"สัตว์กระเพาะเดี่ยว" },
                        { "id": u"สัตว์กระเพาะรวม", "text": u"สัตว์กระเพาะรวม" }
                    ],
                },
                {
                    "id": 2,
                    "name": "sickCount",
                    "title": u"จำนวนสัตว์ป่วย",
                    "type": "integer"
                },

                {
                    "id": 3,
                    "name": "symptom",
                    "title": u"อาการ",
                    "type": "multiple",
                    "items": [
                        { "id": u"หิว", "text": u"หิว" },
                        { "id": u"โหย", "text": u"โหย" },
                        { "id": u"หา", "text": u"หา" }
                    ],
                }
            ]
        })

        #self.state_report = ReportState.objects.create(
        #    report_type=self.report_type,
        #    name='Report',
        #    code='report'
        #)
        self.state_case = ReportState.objects.create(
            report_type=self.report_type,
            name='Case',
            code='case'
        )
        self.state_outbreak = ReportState.objects.create(
            report_type=self.report_type,
            name='Outbreak',
            code='outbreak'
        )

        self.update_state_url = '/report/%s/protect-update-state/must-override-in-settings-local.py/%s/'

    def test_esper_events(self):

        # Install https://bitbucket.org/opendream/podd-cep
        # Grail run-app before this tests

        case_definition = CaseDefinition(
            report_type=self.report_type,
            #from_state=self.state_report,
            to_state=self.state_case,
            epl='sickCount > 3',
            code='test_SickCountMoreThan3',
            drop_if_exists=False
        )
        case_definition.save()

        case_definition = CaseDefinition(
            report_type=self.report_type,
            #from_state=self.state_report,
            to_state=self.state_case,
            epl='sickCount > 10',
            code='test_SickCountMoreThan10',
            drop_if_exists=False
        )
        case_definition.save()

        report1 = factory.create_report(type=self.report_type, form_data={"animalType": u"สัตว์ปีก", "sickCount": 0})
        report2 = factory.create_report(type=self.report_type, form_data={"animalType": u"สัตว์ปีก", "sickCount": 1})
        report3 = factory.create_report(type=self.report_type, form_data={"animalType": u"สัตว์ปีก", "sickCount": 3})

        self.assertEqual(report1.state.code, 'report')
        self.assertEqual(report2.state.code, 'report')
        self.assertEqual(report3.state.code, 'report')

        report4 = factory.create_report(type=self.report_type, form_data={"animalType": u"สัตว์ปีก", "sickCount": 4})
        self.assertEqual(report4.state.code, 'report')
        Client().post(self.update_state_url % (report4.id, 'case')) # mock
        report4 = Report.objects.get(id=report4.id)
        self.assertEqual(report4.state, self.state_case)

        report5 = factory.create_report(type=self.report_type, form_data={"animalType": u"สัตว์ปีก", "sickCount": 5})
        Client().post(self.update_state_url % (report5.id, 'case')) # mock
        report5 = Report.objects.get(id=report5.id)
        self.assertEqual(report5.state, self.state_case)

        report6 = factory.create_report(type=self.report_type, form_data={"animalType": u"สัตว์ปีก", "sickCount": 10})
        Client().post(self.update_state_url % (report6.id, 'outbreak')) # mock
        report6 = Report.objects.get(id=report6.id)
        self.assertEqual(report6.state, self.state_outbreak)

        report7 = factory.create_report(type=self.report_type, form_data={"animalType": u"สัตว์ปีก", "sickCount": 11})
        Client().post(self.update_state_url % (report7.id, 'outbreak')) # mock
        report7 = Report.objects.get(id=report7.id)
        self.assertEqual(report7.state, self.state_outbreak)


    def test_report_type(self):

        authority1 = Authority.objects.create(
            code='chiangmai',
            name='Chiang mai',
        )

        self.report_type.authority = authority1
        self.report_type.save()

        self.assertEqual(list(authority1.report_types.order_by('id')), [self.report_type])


        authority1_1 = Authority.objects.create(
            code='hangdong',
            name='Hangdong',
        )
        authority1_1.inherits.add(authority1)
        self.assertEqual(list(authority1_1.report_types.order_by('id')), [self.report_type])

        # add report type to inherits
        report_type2 = factory.create_report_type(authority=authority1)
        self.assertEqual(list(authority1.report_types.order_by('id')), [self.report_type, report_type2])
        self.assertEqual(list(authority1_1.report_types.order_by('id')), [self.report_type, report_type2])

        report_type3 = factory.create_report_type(authority=authority1)
        authority1_2 = Authority.objects.create(
            code='sarapee',
            name='Sarapee',
        )
        authority1_2.inherits.add(authority1)
        self.assertEqual(list(authority1.report_types.order_by('id')), [self.report_type, report_type2, report_type3])
        self.assertEqual(list(authority1_2.report_types.order_by('id')), [self.report_type, report_type2, report_type3])

        # add report type to children
        report_type4 = factory.create_report_type(authority=authority1_2)
        self.assertEqual(list(authority1.report_types.order_by('id')), [self.report_type, report_type2, report_type3])
        self.assertEqual(list(authority1_1.report_types.order_by('id')), [self.report_type, report_type2, report_type3])
        self.assertEqual(list(authority1_2.report_types.order_by('id')), [self.report_type, report_type2, report_type3, report_type4])

        # remove report type from children
        report_type4.delete()
        self.assertEqual(list(authority1.report_types.order_by('id')), [self.report_type, report_type2, report_type3])
        self.assertEqual(list(authority1_1.report_types.order_by('id')), [self.report_type, report_type2, report_type3])
        self.assertEqual(list(authority1_2.report_types.order_by('id')), [self.report_type, report_type2, report_type3])

        # remove report type from inherit
        report_type2.delete()
        self.assertEqual(list(authority1.report_types.order_by('id')), [self.report_type, report_type3])
        self.assertEqual(list(authority1_1.report_types.order_by('id')), [self.report_type, report_type3])
        self.assertEqual(list(authority1_2.report_types.order_by('id')), [self.report_type, report_type3])


        # get_inherit_report_types

        report_type5 = factory.create_report_type(authority=authority1_2)
        authority1_2_1 = Authority.objects.create(
            code='market1',
            name='Market1',
        )
        authority1_2_1.inherits.add(authority1_2)

        report_type6 = factory.create_report_type(authority=authority1_2_1)

        self.assertEqual(list(authority1_2_1.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type6])

        # multiple inherits
        report_type7 = factory.create_report_type(authority=authority1_1)
        report_type8 = factory.create_report_type(authority=authority1_2)
        authority1_2_1.inherits.add(authority1_1)

        self.assertEqual(list(authority1_2_1.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type6, report_type7, report_type8])

        report_type9 = factory.create_report_type(authority=authority1_2)
        self.assertEqual(list(authority1_2_1.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type6, report_type7, report_type8, report_type9])

        report_type10 = factory.create_report_type(authority=authority1_2_1)
        self.assertEqual(list(authority1_2_1.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type6, report_type7, report_type8, report_type9, report_type10])

        authority1_2_1.inherits.remove(authority1_1)
        self.assertEqual(list(authority1_2_1.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type6, report_type8, report_type9, report_type10])

        report_type11 = factory.create_report_type(authority=authority1)
        self.assertEqual(list(authority1_2_1.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type6, report_type8, report_type9, report_type10, report_type11])

        # circular inherits
        self.assertEqual(list(authority1_1.report_types.order_by('id')), [self.report_type, report_type3, report_type7, report_type11])
        self.assertEqual(list(authority1_2.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type8, report_type9, report_type11])

        authority1_2.inherits.add(authority1_1)
        self.assertEqual(list(authority1_2.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type7, report_type8, report_type9, report_type11])
        self.assertEqual(list(authority1_2_1.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type6, report_type7, report_type8, report_type9, report_type10, report_type11])

        authority1_1.inherits.add(authority1_2)
        self.assertEqual(list(authority1_1.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type7, report_type8, report_type9, report_type11])
        self.assertEqual(list(authority1_2.report_types.order_by('id')), [self.report_type, report_type3, report_type5, report_type7, report_type8, report_type9, report_type11])
        self.assertEqual(list(authority1_1.report_types.order_by('id')), list(authority1_2.report_types.order_by('id')))



    def test_notification(self):

        authority1 = Authority.objects.create(
            code='chiangmai',
            name='Chiang mai',
        )
        a1u1 = factory.create_user()
        a1u2 = factory.create_user()
        a1u3 = factory.create_user()
        authority1.users.add(a1u1, a1u2)

        authority2 = Authority.objects.create(
            code='hangdong',
            name='Hangdong',
        )
        authority2.inherits.add(authority1)
        a2u1 = factory.create_user()
        a2u2 = factory.create_user()
        a2u3 = factory.create_user()
        authority2.users.add(a2u1, a2u2, a2u3)

        authority3 = Authority.objects.create(
            code='sarapee',
            name='Sarapee',
        )
        authority3.inherits.add(authority1)
        a3u1 = factory.create_user()
        a3u2 = factory.create_user()
        a3u3 = factory.create_user()
        authority3.users.add(a2u1, a2u2, a2u3)

        area1 = factory.create_administration_area(authority=authority2)
        area2 = factory.create_administration_area(authority=authority2)
        area3 = factory.create_administration_area(authority=authority3)
        area4 = factory.create_administration_area(authority=authority3)
        area5 = factory.create_administration_area(authority=authority1)
        area6 = factory.create_administration_area()


        template1 = NotificationTemplate.objects.create(
            template=json.dumps({
                'email': {
                    'subject': 'report state {{ report.state_name }}',
                    'body': 'report state {{ report.state_name }} sickCount: {{ report.data.sickCount }}, please contact reporter'
                },
                'sms': 'report state {{ report.state_name }} sickCount: {{ report.data.sickCount }}',
                'gcm': 'report state <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}',
                'default': {
                    'subject': 'report state {{ report.state_name }}',
                    'body': 'report state <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}'
                }
            }),
            condition="report.type_code == '%s' and report.state_code == '%s'" % (self.report_type.code, self.state_case.code),
            description='',
            authority=authority1
        )

        notification_authority1 = NotificationAuthority.objects.create(
            template=template1,
            authority=authority1,
            to='%s, %s' % (a1u1.email, a1u2.username)
        )
        notification_authority2 = NotificationAuthority.objects.create(
            template=template1,
            authority=authority2,
            to='%s, %s, 080-508-8183, external@example.com' % (a2u1.email, a2u2.username)
        )
        notification_authority3 = NotificationAuthority.objects.create(
            template=template1,
            authority=authority3,
            to='%s, %s' % (a3u1.email, a3u2.username)
        )



        report1 = factory.create_report(
            type=self.report_type,
            administration_area=area1,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 3}
        )

        # ====================================================================================
        # Case area 1 and assume sickCount > 3 report auto change to state case
        # ====================================================================================

        report2 = factory.create_report(
            type=self.report_type,
            administration_area=area1,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 4}
        )

        Client().post(self.update_state_url % (report2.id, 'case')) # mock

        # Chiang mai
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).count(), 1)


        # Hangdong
        # self.assertEquals(mail.outbox[0].body, 'report state Case sickCount: 4, please contact reporter')
        # self.assertEquals(mail.outbox[0].to, a2u1.email)
        a2u1_notification = Notification.objects.filter(receive_user=a2u1)[0]
        self.assertEquals(a2u1_notification.receive_user, a2u1)
        self.assertEquals(a2u1_notification.notification_authority, notification_authority2)
        self.assertEquals(a2u1_notification.to, a2u1.email)

        self.assertEqual(Notification.objects.filter(receive_user=a2u2).count(), 1)
        # self.assertEquals(mail.outbox[1].body, 'report state Case sickCount: 4, please contact reporter')
        # self.assertEquals(mail.outbox[1].to, a2u2.email)
        a2u2_notification = Notification.objects.filter(receive_user=a2u2)[0]
        self.assertEquals(a2u2_notification.receive_user, a2u2)
        self.assertEquals(a2u2_notification.notification_authority, notification_authority2)
        self.assertEquals(a2u2_notification.to, a2u2.username)

        self.assertEqual(Notification.objects.filter(receive_user__isnull=True, to='0805088183').count(), 1)
        a2ux_notification = Notification.objects.filter(receive_user__isnull=True, to='0805088183')[0]
        self.assertEquals(a2ux_notification.receive_user, None)
        self.assertEquals(a2ux_notification.notification_authority, notification_authority2)
        self.assertEquals(a2ux_notification.to, '0805088183')

        self.assertEqual(Notification.objects.filter(receive_user__isnull=True, to='external@example.com').count(), 1)
        # self.assertEquals(mail.outbox[2].body, 'report state Case sickCount: 4, please contact reporter')
        # self.assertEquals(mail.outbox[2].to, 'external@example.com')
        a2uy_notification = Notification.objects.filter(receive_user__isnull=True, to='external@example.com')[0]
        self.assertEquals(a2uy_notification.receive_user, None)
        self.assertEquals(a2uy_notification.notification_authority, notification_authority2)
        self.assertEquals(a2uy_notification.to, 'external@example.com')


        # Sarapee
        self.assertEqual(Notification.objects.filter(receive_user=a3u1).count(), 0)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2).count(), 0)
        self.assertEqual(Notification.objects.filter(receive_user=a3u3).count(), 0)


        # ====================================================================================
        # Case area 3 and assume sickCount > 3 report auto change to state case
        # ====================================================================================
        report3 = factory.create_report(
            type=self.report_type,
            administration_area=area3,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 4}
        )
        Client().post(self.update_state_url % (report3.id, 'case')) # mock

        # Chiang mai
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).count(), 0)

        # Hangdong
        self.assertEqual(Notification.objects.filter(receive_user=a2u1).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a2u2).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a2u3).count(), 0)

        # Sarapee
        self.assertEqual(Notification.objects.filter(receive_user=a3u1).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a3u3).count(), 0)


        # ====================================================================================
        # Case area 6 and assume sickCount > 3 report auto change to state case
        # but no responsible area on authority
        # ====================================================================================
        report4 = factory.create_report(
            type=self.report_type,
            administration_area=area6,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 4}
        )
        Client().post(self.update_state_url % (report4.id, 'case'))  # mock

        # Chiang mai
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).count(), 0)

        # Hangdong
        self.assertEqual(Notification.objects.filter(receive_user=a2u1).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a2u2).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a2u3).count(), 0)

        # Sarapee
        self.assertEqual(Notification.objects.filter(receive_user=a3u1).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a3u3).count(), 0)


        # ====================================================================================
        # Case area 2 and Sarapee(area 3, area 4) subscribe Hangdong(area 1, area 2)
        # ====================================================================================

        # Subscribe
        authority3.deep_subscribes.add(authority2)

        report5 = factory.create_report(
            type=self.report_type,
            administration_area=area2,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 4}
        )
        Client().post(self.update_state_url % (report5.id, 'case'))  # mock

        # Chiang mai
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).count(), 3)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).count(), 3)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).count(), 0)

        # Hangdong
        self.assertEqual(Notification.objects.filter(receive_user=a2u1).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a2u2).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a2u3).count(), 0)

        # Sarapee
        self.assertEqual(Notification.objects.filter(receive_user=a3u1).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a3u3).count(), 0)


        # Check receive notification from subscribe authority
        self.assertEqual(Notification.objects.filter(receive_user=a3u1, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a3u3, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 0)

        self.assertEqual(Notification.objects.filter(receive_user=a3u1, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).order_by('id')[0].notification_authority.authority, authority3)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).order_by('id')[0].notification_authority.authority, authority3)

        self.assertEqual(Notification.objects.filter(receive_user=a3u1, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).order_by('id')[0].subscribe_authority, authority2)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).order_by('id')[0].subscribe_authority, authority2)

        # remove user from authority but ignore because check by to field only
        authority3.users.remove(a3u2)
        report6 = factory.create_report(
            type=self.report_type,
            administration_area=area2,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 4}
        )
        Client().post(self.update_state_url % (report6.id, 'case'))  # mock
        # Check receive notification from subscribe authority

        # Chiang mai
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).count(), 4)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).count(), 4)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).count(), 0)
        self.assertEqual(Notification.objects.filter(receive_user=a1u1, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 0)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 0)

        # Hangdong
        self.assertEqual(Notification.objects.filter(receive_user=a2u1).count(), 3)
        self.assertEqual(Notification.objects.filter(receive_user=a2u2).count(), 3)
        self.assertEqual(Notification.objects.filter(receive_user=a2u3).count(), 0)

        # Sarapee
        self.assertEqual(Notification.objects.filter(receive_user=a3u1, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a3u3, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 0)


        # ====================================================================================
        # Case same area 2 and Chiang mai subscribe Hangdong just not send notification to Chiang mai
        # ====================================================================================

        # Subscribe
        authority1.deep_subscribes.add(authority2)

        report6 = factory.create_report(
            type=self.report_type,
            administration_area=area2,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 4}
        )
        Client().post(self.update_state_url % (report6.id, 'case'))  # mock

        # Chiang mai
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).count(), 5)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).count(), 5)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).count(), 0)
        # no subscribe notification
        #self.assertEqual(Notification.objects.filter(receive_user=a1u1, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 1)
        #self.assertEqual(Notification.objects.filter(receive_user=a1u2, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 1)

        # Hangdong
        self.assertEqual(Notification.objects.filter(receive_user=a2u1).count(), 4)
        self.assertEqual(Notification.objects.filter(receive_user=a2u2).count(), 4)
        self.assertEqual(Notification.objects.filter(receive_user=a2u3).count(), 0)


        # Sarapee
        self.assertEqual(Notification.objects.filter(receive_user=a3u1, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 3)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 3)
        self.assertEqual(Notification.objects.filter(receive_user=a3u3, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 0)

        authority1.deep_subscribes.remove(authority2) # !!! unsubscribe here


        # ====================================================================================
        # Case area 2 and Sarapee subscribe Hangdong and Hangdong subscribe Sarapee
        # ====================================================================================

        # Subscribe
        authority2.deep_subscribes.add(authority3)

        report7 = factory.create_report(
            type=self.report_type,
            administration_area=area2,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 4}
        )
        Client().post(self.update_state_url % (report7.id, 'case'))  # mock

        # Chiang mai
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).count(), 6)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).count(), 6)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).count(), 0)

        # Hangdong
        self.assertEqual(Notification.objects.filter(receive_user=a2u1).count(), 5)
        self.assertEqual(Notification.objects.filter(receive_user=a2u2).count(), 5)
        self.assertEqual(Notification.objects.filter(receive_user=a2u3).count(), 0)

        # Sarapee
        self.assertEqual(Notification.objects.filter(receive_user=a3u1, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 4)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 4)
        self.assertEqual(Notification.objects.filter(receive_user=a3u3, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 0)


        # ====================================================================================
        # Reporter Feedback
        # ====================================================================================
        template2 = NotificationTemplate.objects.create(
            template=json.dumps({
                'email': {
                    'subject': 'feedback report {{ report.state_name }}',
                    'body': 'feedback report {{ report.state_name }} sickCount: {{ report.data.sickCount }}, please contact administrator'
                },
                'sms': 'feedback report {{ report.state_name }} sickCount: {{ report.data.sickCount }}',
                'gcm': 'feedback report <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}',
                'default': {
                    'subject': 'feedback report {{ report.state_name }}',
                    'body': 'feedback report<a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}'
                }
            }),
            condition="report.type_code == '%s' and report.state_code == 'report'" % (self.report_type.code),
            description='',
            authority=authority1,
            type=NotificationTemplate.TYPE_REPORTER_FEEDBACK
        )
        NotificationAuthority.objects.create(
            template=template2,
            authority=authority1,
            to='%s, %s,080-508-8183, external@example.com' % (a1u1.email, a1u2.username) # will be ignore in case reporter_feedback
        )

        reporter = factory.create_user()
        report8 = factory.create_report(
            type=self.report_type,
            administration_area=area2,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 4},
            created_by=reporter
        )

        Client().post(self.update_state_url % (report8.id, 'case'))  # mock

        report8 = Report.objects.get(id=report8.id)

        # Chiang mai
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).count(), 7)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).count(), 7)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).count(), 0)

        # Hangdong
        self.assertEqual(Notification.objects.filter(receive_user=a2u1).count(), 6)
        self.assertEqual(Notification.objects.filter(receive_user=a2u2).count(), 6)
        self.assertEqual(Notification.objects.filter(receive_user=a2u3).count(), 0)

        # Sarapee
        self.assertEqual(Notification.objects.filter(receive_user=a3u1, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 5)
        self.assertEqual(Notification.objects.filter(receive_user=a3u2, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 5)
        self.assertEqual(Notification.objects.filter(receive_user=a3u3, type=NEWS_TYPE_SUBSCRIBE_AUTHORITY).count(), 0)

        # Reporter
        self.assertEqual(Notification.objects.filter(receive_user=reporter).count(), 1)
        self.assertEqual(
            Notification.objects.filter(receive_user=reporter)[0].render_web_message(),
            'feedback report<a href="link-to-report">%s</a> sickCount: %s' % (report8.state_name, report8.data.sickCount)
        )


        template3 = NotificationTemplate.objects.create(
            template=json.dumps({
                'email': {
                    'subject': 'feedback report template3 {{ report.state_name }}',
                    'body': 'feedback report template3 {{ report.state_name }} sickCount: {{ report.data.sickCount }}, please contact administrator'
                },
                'sms': 'feedback report template3 {{ report.state_name }} sickCount: {{ report.data.sickCount }}',
                'gcm': 'feedback report template3 <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}',
                'default': {
                    'subject': 'feedback report template3 {{ report.state_name }}',
                    'body': 'feedback report template3 <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}'
                }
            }),
            condition="report.type_code == '%s' and report.state_code == 'report'" % (self.report_type.code),
            description='',
            authority=authority2,
            type=NotificationTemplate.TYPE_REPORTER_FEEDBACK
        )
        NotificationAuthority.objects.create(
            template=template3,
            authority=authority2,
            to='%s, %s' % (a2u1.email, a2u2.username) # will be ignore in case reporter_feedback
        )

        report9 = factory.create_report(
            type=self.report_type,
            administration_area=area4,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 1},
            created_by=reporter
        )
        self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 2)
        self.assertEqual(
            Notification.objects.filter(receive_user=reporter).order_by('id')[1].render_web_message(),
            'feedback report<a href="link-to-report">%s</a> sickCount: %s' % (report9.state_name, report9.data.sickCount)
        )

        report10 = factory.create_report(
            type=self.report_type,
            administration_area=area2,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 1},
            created_by=reporter
        )
        self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 4)


    def test_reporter_feedback_enable(self):
        authority1 = Authority.objects.create(
            code='chiangmai',
            name='Chiang mai',
        )

        authority2 = Authority.objects.create(
            code='hangdong',
            name='Hangdong',
        )
        authority2.inherits.add(authority1)

        authority3 = Authority.objects.create(
            code='sarapee',
            name='Sarapee',
        )
        authority3.inherits.add(authority1)

        template1 = NotificationTemplate.objects.create(template='Ignore', condition='False', type=NotificationTemplate.TYPE_REPORTER_FEEDBACK, authority=authority1)
        template2 = NotificationTemplate.objects.create(template='Ignore', condition='False', type=NotificationTemplate.TYPE_REPORTER_FEEDBACK, authority=authority2)
        template3 = NotificationTemplate.objects.create(template='Ignore', condition='False', type=NotificationTemplate.TYPE_REPORTER_FEEDBACK, authority=authority3)

        # Initial
        #self.assertEqual(template1.can_edit(authority1), True)
        #self.assertEqual(template1.can_edit(authority2), False)
        #self.assertEqual(template1.can_edit(authority3), False)

        #self.assertEqual(template2.can_edit(authority1), False)
        #self.assertEqual(template2.can_edit(authority2), True)
        #self.assertEqual(template2.can_edit(authority3), False)

        #self.assertEqual(template3.can_edit(authority1), False)
        #self.assertEqual(template3.can_edit(authority2), False)
        #self.assertEqual(template3.can_edit(authority3), True)

        self.assertEqual(template1.can_disable(authority1), True)
        self.assertEqual(template1.can_disable(authority2), False)
        self.assertEqual(template1.can_disable(authority3), False)

        self.assertEqual(template2.can_disable(authority1), False)
        self.assertEqual(template2.can_disable(authority2), True)
        self.assertEqual(template2.can_disable(authority3), False)

        self.assertEqual(template3.can_disable(authority1), False)
        self.assertEqual(template3.can_disable(authority2), False)
        self.assertEqual(template3.can_disable(authority3), True)

        self.assertEqual(template1.enabled(authority1), False)
        self.assertEqual(template1.enabled(authority2), False)
        self.assertEqual(template1.enabled(authority3), False)

        self.assertEqual(template2.enabled(authority1), False)
        self.assertEqual(template2.enabled(authority2), False)
        self.assertEqual(template2.enabled(authority3), False)

        self.assertEqual(template3.enabled(authority1), False)
        self.assertEqual(template3.enabled(authority2), False)
        self.assertEqual(template3.enabled(authority3), False)

        # enable all children
        template1.enable(authority1)
        self.assertEqual(template1.enabled(authority1), True)
        self.assertEqual(template1.enabled(authority2), True)
        self.assertEqual(template1.enabled(authority3), True)

        self.assertEqual(template2.enabled(authority1), False)
        self.assertEqual(template2.enabled(authority2), False)
        self.assertEqual(template2.enabled(authority3), False)

        self.assertEqual(template3.enabled(authority1), False)
        self.assertEqual(template3.enabled(authority2), False)
        self.assertEqual(template3.enabled(authority3), False)

        template2.enable(authority2)
        self.assertEqual(template1.enabled(authority1), True)
        self.assertEqual(template1.enabled(authority2), True)
        self.assertEqual(template1.enabled(authority3), True)

        self.assertEqual(template2.enabled(authority1), False)
        self.assertEqual(template2.enabled(authority2), True)
        self.assertEqual(template2.enabled(authority3), False)

        self.assertEqual(template3.enabled(authority1), False)
        self.assertEqual(template3.enabled(authority2), False)
        self.assertEqual(template3.enabled(authority3), False)

        # can't disable
        template1.disable(authority2)
        self.assertEqual(template1.enabled(authority2), True)

        # can disable
        template2.disable(authority2)
        self.assertEqual(template2.enabled(authority2), False)

        # disable all children
        template1.disable(authority1)
        self.assertEqual(template1.enabled(authority1), False)
        self.assertEqual(template1.enabled(authority2), False)
        self.assertEqual(template1.enabled(authority3), False)

        # fork from parent
        template2.enable(authority2)

        authority1.inherits.add(authority2) # circular

        oid = template2.id
        template2.enable(authority1)

        template_forked = template2
        template2 = NotificationTemplate.objects.get(id=oid)

        self.assertEqual(template_forked.id, template3.id+1)
        self.assertEqual(template_forked.authority, authority1)
        self.assertEqual(template_forked.enabled(authority1), True)
        self.assertEqual(template_forked.enabled(authority2), True)
        self.assertEqual(template_forked.enabled(authority3), True)

        self.assertEqual(template2.enabled(authority2), False) # Auto disable child
        self.assertEqual(template2.can_disable(authority2), True)

        self.assertEqual(template1.can_disable(authority2), False) # Transfer permission
        self.assertEqual(template1.can_disable(authority1), True)


    def test_follow_up(self):


        authority1 = Authority.objects.create(
            code='chiangmai',
            name='Chiang mai',
        )
        a1u1 = factory.create_user()
        a1u2 = factory.create_user()
        authority1.users.add(a1u1, a1u2)

        authority2 = Authority.objects.create(
            code='hangdong',
            name='Hangdong',
        )
        authority2.inherits.add(authority1)
        a2u1 = factory.create_user()
        a2u2 = factory.create_user()
        a2u3 = factory.create_user()
        authority2.users.add(a2u1, a2u2, a2u3)

        authority3 = Authority.objects.create(
            code='sarapee',
            name='Sarapee',
        )
        authority3.inherits.add(authority1)
        a3u1 = factory.create_user()
        a3u2 = factory.create_user()
        a3u3 = factory.create_user()
        authority3.users.add(a2u1, a2u2, a2u3)

        area1 = factory.create_administration_area(authority=authority1)
        area2 = factory.create_administration_area(authority=authority2)
        area3 = factory.create_administration_area(authority=authority2)
        area4 = factory.create_administration_area(authority=authority3)
        area5 = factory.create_administration_area(authority=authority3)


        report_type1 = factory.create_report_type(name='TestFollowUp', code='TestFollowUp', form_definition={
            "startPageId": 1,
            "questions": [
                {
                    "id": 1,
                    "name": "animalType",
                    "title": u"ประเภทสัตว์",
                    "type": "single",
                    "items": [
                        {"id": u"สัตว์ปีก", "text": u"สัตว์ปีก"},
                        {"id": u"สัตว์กระเพาะเดี่ยว", "text": u"สัตว์กระเพาะเดี่ยว"},
                        {"id": u"สัตว์กระเพาะรวม", "text": u"สัตว์กระเพาะรวม"}
                    ],
                },
                {
                    "id": 2,
                    "name": "sickCount",
                    "title": u"จำนวนสัตว์ป่วย",
                    "type": "integer"
                },

                {
                    "id": 3,
                    "name": "symptom",
                    "title": u"อาการ",
                    "type": "multiple",
                    "items": [
                        {"id": u"หิว", "text": u"หิว"},
                        {"id": u"โหย", "text": u"โหย"},
                        {"id": u"หา", "text": u"หา"}
                    ],
                }
            ]
        })

        state_case = ReportState.objects.create(
            report_type=report_type1,
            name='Case',
            code='case'
        )
        state_outbreak = ReportState.objects.create(
            report_type=report_type1,
            name='Outbreak',
            code='outbreak'
        )

        template1 = NotificationTemplate.objects.create(
            template=json.dumps({
                'email': {
                    'subject': 'follow up report template1 {{ report.state_name }}',
                    'body': 'follow up report template1 {{ report.state_name }} sickCount: {{ report.data.sickCount }}, please contact administrator'
                },
                'sms': 'follow up report template1 {{ report.state_name }} sickCount: {{ report.data.sickCount }}',
                'gcm': 'follow up report template1 <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}',
                'default': {
                    'subject': 'follow up report template1 {{ report.state_name }}',
                    'body': 'follow up report template1 <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}'
                }
            }),
            condition="report.type_code == '%s' and report.state_code == 'case' and report.parent is None" % (report_type1.code),
            description='',
            authority=authority1,
            type=NotificationTemplate.TYPE_NOTIFY_FOLLOW_UP,
            trigger_pattern='0000100001000100101',
            trigger_delay_days=2
        )
        template1.enable(authority1)

        template2 = NotificationTemplate.objects.create(
            template=json.dumps({
                'email': {
                    'subject': 'follow up late report template2 {{ report.state_name }}',
                    'body': 'follow up late report template2 {{ report.state_name }} sickCount: {{ report.data.sickCount }}, please contact administrator'
                },
                'sms': 'follow up late report template2 {{ report.state_name }} sickCount: {{ report.data.sickCount }}',
                'gcm': 'follow up late report template2 <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}',
                'default': {
                    'subject': 'follow up late report template2 {{ report.state_name }}',
                    'body': 'follow up late report template1 <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}'
                }
            }),
            #condition="report.type_code == '%s' and report.state_code == 'case' and report.parent is None" % (report_type1.code),
            description='',
            authority=authority1,
            type=NotificationTemplate.TYPE_LATE_FOLLOW_UP,
            trigger_notify_follow_up=template1
        )
        template2.enable(authority1, '%s, %s' % (a1u1.email, a1u2.username))

        template3 = NotificationTemplate.objects.create(
            template=json.dumps({
                'email': {
                    'subject': 'report state {{ report.state_name }}',
                    'body': 'report state {{ report.state_name }} sickCount: {{ report.data.sickCount }}, please contact reporter'
                },
                'sms': 'report state {{ report.state_name }} sickCount: {{ report.data.sickCount }}',
                'gcm': 'report state <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}',
                'default': {
                    'subject': 'report state {{ report.state_name }}',
                    'body': 'report state <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}'
                }
            }),
            condition="report.type_code == '%s' and report.state_code == 'case' and report.parent is None" % (self.report_type.code),
            description='',
            authority=authority1
        )


        reporter = factory.create_user()


        report1 = factory.create_report(
            type=report_type1,
            administration_area=area4,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 1},
            created_by=reporter
        )
        Client().post(self.update_state_url % (report1.id, 'case'))  # mock
        report1 = Report.objects.get(id=report1.id)

        mpd = settings.MINUTES_PER_DAY
        today = timezone.now()

        with freeze_time(today + datetime.timedelta(minutes=mpd*4)): # 0100001000100101
            send_alert_follow_up.delay()
            send_alert_follow_up.delay() # Check cron can run many time per day
            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 0)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 0)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 0)


        with freeze_time(today + datetime.timedelta(minutes=mpd*5)): # 100001000100101 ##### Reporter

            template1.disable(authority1) # Test disable not send followup to reporter

            send_alert_follow_up.delay()
            send_alert_follow_up.delay()  # Check cron can run many time per day

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 0)

            template1.enable(authority1)

            send_alert_follow_up.delay()
            send_alert_follow_up.delay()  # Check cron can run many time per day

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 0)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 0)

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id')[0].notification_authority.template.type, NotificationTemplate.TYPE_NOTIFY_FOLLOW_UP)
            self.assertEqual(
                Notification.objects.filter(receive_user=reporter).order_by('id')[0].render_web_message(),
                'follow up report template1 <a href="link-to-report">%s</a> sickCount: %s' % (
                    report1.state_name, report1.data.sickCount)
            )


        with freeze_time(today + datetime.timedelta(minutes=mpd*6)): # 00001000100101
            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 0)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 0)

        with freeze_time(today + datetime.timedelta(minutes=mpd*7)): # 0001000100101 ##### Late

            #template2.disable(authority1)  # Test disable not send followup to reporter

            #send_alert_follow_up.delay()
            #send_alert_follow_up.delay()  # Check cron can run many time per day

            #self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 0)
            #self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 0)

            # Undo disabled
            #FollowUp.objects.filter(deadline__gt=yesterday, deadline__lte=today, late_notified=True).update(late_notified=False)

            #template2.enable(authority1, '%s, %s' % (a1u1.email, a1u2.username))  # Test enable send followup to reporter

            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id')[0].notification_authority.template.type, NotificationTemplate.TYPE_LATE_FOLLOW_UP)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id')[0].notification_authority.template.type, NotificationTemplate.TYPE_LATE_FOLLOW_UP)


        with freeze_time(today + datetime.timedelta(minutes=mpd*8)): # 001000100101
            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 1)

        with freeze_time(today + datetime.timedelta(minutes=mpd*9)): # 01000100101
            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 1)

        with freeze_time(today + datetime.timedelta(minutes=mpd*10)): # 1000100101 ##### Reporter
            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 2)
            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id')[1].notification_authority.template.type, NotificationTemplate.TYPE_NOTIFY_FOLLOW_UP)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 1)

        with freeze_time(today + datetime.timedelta(minutes=mpd*11)): # 000100101
            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 2)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 1)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 1)

        with freeze_time(today + datetime.timedelta(minutes=mpd*12)): # 00100101 ##### Late

            template3.enable(authority1, '%s, %s' % (a1u1.email, a1u2.username))

            report2 = factory.create_report(
                type=self.report_type,
                administration_area=area4,
                form_data={"animalType": u"สัตว์ปีก", "sickCount": 1},
                created_by=reporter
            )
            Client().post(self.update_state_url % (report2.id, 'case'))  # mock
            report2 = Report.objects.get(id=report2.id)

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 2)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 2)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id')[1].notification_authority.template.type, NotificationTemplate.TYPE_REPORT)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 2)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id')[1].notification_authority.template.type, NotificationTemplate.TYPE_REPORT)


            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 2)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id')[2].notification_authority.template.type, NotificationTemplate.TYPE_LATE_FOLLOW_UP)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id')[2].notification_authority.template.type, NotificationTemplate.TYPE_LATE_FOLLOW_UP)


        with freeze_time(today + datetime.timedelta(minutes=mpd*13)): # 0100101
            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 2)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 3)


        with freeze_time(today + datetime.timedelta(minutes=mpd*14)): # 100101 ##### Reporter but response form
            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 3)


            response_report1 = factory.create_report(
                type=report_type1,
                administration_area=area4,
                form_data={"animalType": u"สัตว์ปีก", "sickCount": 2},
                created_by=reporter,
                parent=report1
            )
            Client().post(self.update_state_url % (report1.id, 'case'))  # mock
            report1 = Report.objects.get(id=report1.id)
            response_report1 = Report.objects.get(id=response_report1.id)

        with freeze_time(today + datetime.timedelta(minutes=mpd*15)): # 00101

            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 3)

        with freeze_time(today + datetime.timedelta(minutes=mpd*16)): # 0101 ##### not Late

            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 3)

        with freeze_time(today + datetime.timedelta(minutes=mpd*17)): # 101 #### Reporter

            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 4)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 3)

        with freeze_time(today + datetime.timedelta(minutes=mpd*18)): # 01
            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 4)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 3)

        with freeze_time(today + datetime.timedelta(minutes=mpd*19)): # 1 #### State change by admin, clear follow up and not send notify follow up

            Client().post(self.update_state_url % (report1.id, 'outbreak'))  # mock

            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 4)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 3)

        with freeze_time(today + datetime.timedelta(minutes=mpd*20)): #00
            send_alert_follow_up.delay()
            send_alert_follow_up.delay()

            self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 4)
            self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 3)
            self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 3)


    def test_state_change_duplicate(self):
        authority1 = Authority.objects.create(
            code='chiangmai',
            name='Chiang mai',
        )
        a1u1 = factory.create_user()
        a1u2 = factory.create_user()
        a1u3 = factory.create_user()
        authority1.users.add(a1u1, a1u2)

        area1 = factory.create_administration_area(authority=authority1)

        template1 = NotificationTemplate.objects.create(
            template=json.dumps({
                'email': {
                    'subject': 'report state {{ report.state_name }}',
                    'body': 'report state {{ report.state_name }} sickCount: {{ report.data.sickCount }}, please contact reporter'
                },
                'sms': 'report state {{ report.state_name }} sickCount: {{ report.data.sickCount }}',
                'gcm': 'report state <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}',
                'default': {
                    'subject': 'report state {{ report.state_name }}',
                    'body': 'report state <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}'
                }
            }),
            condition="report.type_code == '%s' and report.state_code == '%s'" % (
                self.report_type.code, self.state_case.code),
            description='',
            authority=authority1
        )

        notification_authority1 = NotificationAuthority.objects.create(
            template=template1,
            authority=authority1,
            to='%s, %s' % (a1u1.email, a1u2.username)
        )

        template2 = NotificationTemplate.objects.create(
            template=json.dumps({
                'email': {
                    'subject': 'report state {{ report.state_name }}',
                    'body': 'report state {{ report.state_name }} sickCount: {{ report.data.sickCount }}, please contact reporter'
                },
                'sms': 'report state {{ report.state_name }} sickCount: {{ report.data.sickCount }}',
                'gcm': 'report state <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}',
                'default': {
                    'subject': 'report state {{ report.state_name }}',
                    'body': 'report state <a href="link-to-report">{{ report.state_name }}</a> sickCount: {{ report.data.sickCount }}'
                }
            }),
            condition="report.type_code == '%s' and report.state_code == '%s'" % (
                self.report_type.code, self.state_outbreak.code),
            description='',
            authority=authority1
        )

        notification_authority2 = NotificationAuthority.objects.create(
            template=template2,
            authority=authority1,
            to='%s, %s' % (a1u1.email, a1u3.username)
        )

        reporter = factory.create_user()
        report1 = factory.create_report(
            type=self.report_type,
            administration_area=area1,
            form_data={"animalType": u"สัตว์ปีก", "sickCount": 1},
            created_by=reporter
        )

        Client().post(self.update_state_url % (report1.id, 'case'))  # mock
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).order_by('id').count(), 0)
        self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 0)

        Client().post(self.update_state_url % (report1.id, 'outbreak'))  # mock
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).order_by('id').count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 0)

        Client().post(self.update_state_url % (report1.id, 'case'))  # mock
        self.assertEqual(Notification.objects.filter(receive_user=a1u1).order_by('id').count(), 2)
        self.assertEqual(Notification.objects.filter(receive_user=a1u2).order_by('id').count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=a1u3).order_by('id').count(), 1)
        self.assertEqual(Notification.objects.filter(receive_user=reporter).order_by('id').count(), 0)




    def test_area(self):
        authority1 = Authority.objects.create(
            code='chiangmai',
            name='Chiang mai',
        )

        authority2 = Authority.objects.create(
            code='hangdong',
            name='Hangdong',
        )
        authority2.inherits.add(authority1)

        authority3 = Authority.objects.create(
            code='sarapee',
            name='Sarapee',
        )
        authority3.inherits.add(authority1)

        authority4 = Authority.objects.create(
            code='ignore',
            name='Ignore',
        )

        area11 = factory.create_administration_area(authority=authority1, name='chiangmai-1')
        area21 = factory.create_administration_area(authority=authority2, name='hangdong-1')
        area22 = factory.create_administration_area(authority=authority2, name='hangdong-2')
        area31 = factory.create_administration_area(authority=authority3, name='sarapee-1')
        area32 = factory.create_administration_area(authority=authority3, name='sarapee-2')
        area41 = factory.create_administration_area(authority=authority4, name='ignore-1')
        area42 = factory.create_administration_area(authority=authority4, name='ignore-2')


        # deprecate change to neo4j records
        self.assertEqual(list(authority1.administration_areas.order_by('id')), [area11, area21, area22, area31, area32])
        self.assertEqual(list(authority2.administration_areas.order_by('id')), [area21, area22])
        self.assertEqual(list(authority3.administration_areas.order_by('id')), [area31, area32])
        self.assertEqual(list(authority4.administration_areas.order_by('id')), [area41, area42])



    def test_created_by_save_users(self):
        user1 = factory.create_user()
        authority1 = Authority.objects.create(
            code='hangdong',
            name='Hangdong',
            created_by=user1
        )
        self.assertEqual(list(authority1.users.all()), [user1])

        user2 = factory.create_user()
        authority2 = Authority.objects.create(
            code='sarapee',
            name='Sarapee',
            created_by=user2
        )
        self.assertEqual(list(authority2.users.all()), [user2])

        authority1.users.remove(user1)
        self.assertEqual(list(authority1.users.all()), [])

        authority1.save()
        authority1 = Authority.objects.get(id=authority1.id)
        self.assertEqual(list(authority1.users.all()), [])

    def test_adjust_incident_date(self):
        report = factory.create_report()

        now = datetime.datetime.now()
        one_second = datetime.timedelta(seconds=1)
        delta = datetime.timedelta(days=60)
        test_date = now - delta

        # nothing happen if date is not reach the threshold
        report.date = now
        report.incident_date = now.date()
        report.adjust_incident_date()

        # report.date must be timezone-aware
        self.assertTrue(timezone.is_aware(report.date))
        self.assertEqual(report.date, timezone.make_aware(now, timezone.utc))
        self.assertEqual(report.incident_date, now.date())

        report.date = test_date
        report.incident_date = test_date.date()
        # start to adjust date.
        report.adjust_incident_date()

        self.assertLess(timezone.make_naive(report.date, timezone.utc) - now, one_second)
        self.assertEqual(report.incident_date, now.date())

        # form data must be modified
        form_data = json.loads(report.form_data)
        self.assertEqual(form_data['_invalid_report_date'], str(timezone.make_aware(test_date, timezone.utc)))
        self.assertEqual(form_data['_invalid_report_incident_date'], str(test_date.date()))

    def test_add_comment_to_parent(self):
        report = factory.create_report()

        # check number of comment before follow-up report happen.
        comments = ReportComment.objects.filter(report=report)
        previous_comment_count = comments.count()

        followup_report = factory.create_report(parent=report)

        comments = ReportComment.objects.filter(report=report).order_by('-id')
        current_comment_count = comments.count()

        self.assertGreater(current_comment_count, previous_comment_count)

def common_public_setup(self):

    self.authority = Authority.objects.create(name='Public', code='public')
    self.report_type = factory.create_report_type(authority=self.authority)
    self.user = factory.create_user(username="user", display_password='password', status=USER_STATUS_ADDITION_VOLUNTEER,
                                    is_anonymous=False, is_public=True)
    self.anonymous = factory.create_user(username="anonymous", display_password='password',
                                         status=USER_STATUS_ADDITION_VOLUNTEER, is_anonymous=True, is_public=True)
    self.authority.users.add(self.user)
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


class TestPublic(TestCase):

    def setUp(self):
        common_public_setup(self)


    def test_report_default_fields(self):

        error = False
        try:
            factory.create_report(type=self.report_type, created_by=self.anonymous, add_default_administration_area=False)
        except Exception as e:
            error = True
            self.assertEqual(e.message, 'Anonymous can not create report')

        self.assertTrue(error)


        report = factory.create_report(type=self.report_type, created_by=self.user, add_default_administration_area=False)

        self.assertEqual(report.administration_area.code, 'public_%s' % settings.CURRENT_DOMAIN_ID)
        self.assertEqual(report.is_public, True)

        error = False
        try:
            factory.create_report(type=self.report_type, created_by=self.user, report_location=None, add_default_report_location=False)
        except Exception as e:
            error = True
            self.assertEqual(e.message, 'Public report location required')

        self.assertTrue(error)

    def test_assign_administration_area(self):
        admin_area = AdministrationArea.objects.create(
            name="admin_area1",
            mpoly=self.administration_area_mpoly,
            location=self.administration_area_location,
            authority=self.authority,
            code='public_%s' % settings.CURRENT_DOMAIN_ID
        )

        report = Report(
            report_location=admin_area.location,
            created_by=self.user,
            is_public=True,
            domain_id=settings.CURRENT_DOMAIN_ID
        )
        report.assign_administration_area()
        self.assertEqual(report.administration_area.id, admin_area.id)

    def test_auto_assign_administration_area_if_is_public_report(self):
        admin_area = AdministrationArea.objects.create(
            name="admin_area1",
            mpoly=self.administration_area_mpoly,
            location=self.administration_area_location,
            authority=self.authority,
            code='public_%s' % settings.CURRENT_DOMAIN_ID
        )

        report = Report.objects.create(
            report_id=100001,
            guid="100001",
            type=self.report_type,
            created_by=self.user,
            date=datetime.datetime.now(),
            incident_date=datetime.datetime.now(),
            form_data="{}",
            negative=True,
            report_location=admin_area.location,
            domain_id=settings.CURRENT_DOMAIN_ID
        )

        report = Report.objects.get(id=report.id)
        self.assertEqual(report.administration_area.id, admin_area.id)

    def test_action_allow(self):

        report = factory.create_report(type=self.report_type, created_by=self.user)

        error = False
        try:
            ReportComment.objects.create(report=report, created_by=self.anonymous, message='Hello')
        except Exception as e:
            error = True
            self.assertEqual(e.message, 'Not allow created by anonymous')

        self.assertTrue(error)

        error = False
        try:
            ReportLike.objects.create(report=report, created_by=self.anonymous)
        except Exception as e:
            error = True
            self.assertEqual(e.message, 'Not allow created by anonymous')

        self.assertTrue(error)

        error = False
        try:
            ReportMeToo.objects.create(report=report, created_by=self.anonymous)
        except Exception as e:
            error = True
            self.assertEqual(e.message, 'Not allow created by anonymous')

        self.assertTrue(error)


    def test_action_count(self):

        user1 = factory.create_user(display_password='password', status=USER_STATUS_ADDITION_VOLUNTEER, is_anonymous=False, is_public=True)
        user2 = factory.create_user(display_password='password', status=USER_STATUS_ADDITION_VOLUNTEER, is_anonymous=False, is_public=True)


        report = factory.create_report(type=self.report_type, created_by=self.user)


        # Comment
        comment1 = ReportComment.objects.create(report=report, created_by=user1, message='Hello 1')
        report = Report.objects.get(id=report.id)
        self.assertEqual(report.comment_count, 1)


        comment2 = ReportComment.objects.create(report=report, created_by=user1, message='Hello 2')
        report = Report.objects.get(id=report.id)
        self.assertEqual(report.comment_count, 2)

        comment2.delete()
        report = Report.objects.get(id=report.id)
        self.assertEqual(report.comment_count, 1)

        # Like
        like1 = ReportLike.objects.create(report=report, created_by=user1)
        report = Report.objects.get(id=report.id)
        self.assertEqual(report.like_count, 1)
        self.assertEqual(report.get_like(user1), like1)


        like2 = ReportLike.objects.create(report=report, created_by=user2)
        report = Report.objects.get(id=report.id)
        self.assertEqual(report.like_count, 2)
        self.assertEqual(report.get_like(user2), like2)

        like2 = ReportLike.objects.get(id=like2.id)
        like2.delete()
        report = Report.objects.get(id=report.id)
        self.assertEqual(report.like_count, 1)
        self.assertIsNone(report.get_like(user2))


        # Me Too
        me_too1 = ReportMeToo.objects.create(report=report, created_by=user1)
        report = Report.objects.get(id=report.id)
        self.assertEqual(report.me_too_count, 1)
        self.assertEqual(report.get_me_too(user1), me_too1)


        me_too2 = ReportMeToo.objects.create(report=report, created_by=user2)
        report = Report.objects.get(id=report.id)
        self.assertEqual(report.me_too_count, 2)
        self.assertEqual(report.get_me_too(user2), me_too2)

        me_too2 = ReportMeToo.objects.get(id=me_too2.id)
        me_too2.delete()
        report = Report.objects.get(id=report.id)
        self.assertEqual(report.me_too_count, 1)
        self.assertIsNone(report.get_me_too(user2))

    def test_not_auto_assign_administration_area_if_is_not_public_report(self):
        admin_area = AdministrationArea.objects.create(
            name="admin_area1",
            mpoly=self.administration_area_mpoly,
            location=self.administration_area_location,
            authority=self.authority
        )

        try:
            private_user = factory.create_user("Jaguar")
            report = Report.objects.create(
                report_id=100001,
                guid="100001",
                type=self.report_type,
                created_by=private_user,
                date=datetime.datetime.now(),
                incident_date=datetime.datetime.now(),
                form_data="{}",
                negative=True,
                report_location=admin_area.location
            )
        except:
            report = None

        self.assertIsNone(report)

    def test_public_report_will_add_to_public_feed(self):
        admin_area = AdministrationArea.objects.create(
            name="admin_area1",
            mpoly=self.administration_area_mpoly,
            location=self.administration_area_location,
            authority=self.authority
        )

        redis = get_redis_connection()
        ''':type redis: redis.client.StrictRedis'''
        redis.flushall()

        report = Report.objects.create(
            report_id=100001,
            guid="100001",
            type=self.report_type,
            created_by=self.user,
            date=datetime.datetime.now(),
            incident_date=datetime.datetime.now(),
            form_data="{}",
            negative=True,
            report_location=admin_area.location,
        )

        self.assertEqual(redis.zcard(report.get_public_feed_key()), 1)

    def test_private_report_will_not_add_to_public_feed(self):
        admin_area = AdministrationArea.objects.create(
            name="admin_area1",
            mpoly=self.administration_area_mpoly,
            location=self.administration_area_location,
            authority=self.authority
        )

        redis = get_redis_connection()
        ''':type redis: redis.client.StrictRedis'''
        redis.flushall()

        private_user = factory.create_user("Jaguar")
        report = Report.objects.create(
            report_id=100001,
            guid="100001",
            type=self.report_type,
            created_by=private_user,
            date=datetime.datetime.now(),
            incident_date=datetime.datetime.now(),
            form_data="{}",
            negative=True,
            report_location=admin_area.location,
            administration_area=admin_area,
            administration_location=admin_area.location,
        )

        self.assertEqual(redis.zcard(report.get_public_feed_key()), 0)

    def test_deleted_report_will_be_remove_from_public_feed(self):
        admin_area = AdministrationArea.objects.create(
            name="admin_area1",
            mpoly=self.administration_area_mpoly,
            location=self.administration_area_location,
            authority=self.authority
        )

        another_admin_area = AdministrationArea.objects.create(
            name="admin_area2",
            mpoly=self.administration_area_mpoly,
            location=self.administration_area_location,
            authority=self.authority
        )

        redis = get_redis_connection()
        ''':type redis: redis.client.StrictRedis'''
        redis.flushall()

        report = Report.objects.create(
            report_id=200001,
            guid="200001",
            type=self.report_type,
            created_by=self.user,
            date=datetime.datetime.now(),
            incident_date=datetime.datetime.now(),
            form_data="{}",
            negative=True,
            report_location=admin_area.location
        )
        report.curated_in.add(another_admin_area)
        report._add_to_public_feed(get_public_feed_key(another_admin_area))

        self.assertEqual(redis.zcard(report.get_public_feed_key()), 1)
        self.assertEqual(redis.zcard(get_public_feed_key(another_admin_area)), 1)

        report = Report.objects.get(id=report.id)
        report.delete()
        self.assertEqual(redis.zcard(report.get_public_feed_key()), 0)
        self.assertEqual(redis.zcard(get_public_feed_key(another_admin_area)), 0)
