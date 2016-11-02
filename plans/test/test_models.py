# -*- encoding: utf-8 -*-
import json
from django.test import TestCase
from mockredis import mock_strict_redis_client

import mock
from accounts.models import Authority
from common import factory
from plans.models import Plan, PlanLevel, PlanReport
from reports.models import ReportState, Report, ReportComment
from notifications.models import NotificationTemplate, Notification


@mock.patch('django_redis.get_redis_connection', mock_strict_redis_client)
class TestSafety(TestCase):

    def setUp(self):

        self.report_type = factory.create_report_type(name='TestReportType', code='TestReportType', form_definition={})
        self.report_type_ignore = factory.create_report_type(name='TestReportTypeIgnore', code='TestReportTypeIgnore', form_definition={})

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
        self.state_suspect_outbreak = ReportState.objects.create(
            report_type=self.report_type,
            name='Suspect Outbreak',
            code='suspect-outbreak'
        )

        self.state_outbreak_ignore = ReportState.objects.create(
            report_type=self.report_type_ignore,
            name='Outbreak',
            code='outbreak'
        )

        self.plan = Plan.objects.create(
            name="Animal sick/dead outbreak",
            code="animalSickeDeadOutbreak",
            condition="report.type.code == '%s' and report.state_code == '%s'" % (self.report_type.code, self.state_outbreak.code)
        )

        PlanLevel.objects.create(plan=self.plan, name='Red', code='red', distance=1)
        PlanLevel.objects.create(plan=self.plan, name='Yellow', code='yellow', distance=900)
        PlanLevel.objects.create(plan=self.plan, name='Green', code='green', distance=2400)


        self.authority_livestock = Authority.objects.create(
            code='livestock',
            name='Livestock'
        )

        self.authority_local1 = Authority.objects.create(
            code='local1',
            name='Local 1'
        )
        self.authority_local1.inherits.add(self.authority_livestock)

        self.authority_local2 = Authority.objects.create(
            code='local2',
            name='Local 2'
        )
        self.authority_local2.inherits.add(self.authority_livestock)

        # TODO: add mpoly to each areas

        self.area_red1    = factory.create_administration_area(
            name='San Ma Fuang',
            authority=self.authority_local1,
            contacts=u'{"headman": "นายอำพล 081234510"}',
            location='0101000020E610000094986F9635CB58406FF940D931D63340',
            mpoly='0106000020E61000000100000001030000000100000005000000D433AA18A4CB5840543ADFF0E6D43340F7C5624AC5CA5840424BB0129DD53340BB159EBD23CB58402501C2E41BD7334033C777F4BECB5840F19BE50EA2D53340D433AA18A4CB5840543ADFF0E6D43340'
        )
        self.area_yellow1 = factory.create_administration_area(
            name='Pang Sak',
            authority=self.authority_local1,
            contacts=u'{"headman": "นายศร 08-1234-521 (ผู้ใหญ่บ้าน หมู่ 1)", "volunteer": "หมู่ 1 นายกร 08 123 4522, 0812345ก23"}',
            location='0101000020E610000005BD1EE95FCB58407067570848D73340',
            mpoly='0106000020E6100000010000000103000000010000000600000033C777F4BECB5840F19BE50EA2D53340BB159EBD23CB58402501C2E41BD73340E9C77CC729CB5840D22E947EF7D833405E3B0A2927CC5840B06F4B81B1D8334094C547082DCC5840A587959543D7334033C777F4BECB5840F19BE50EA2D53340'
        )
        self.area_yellow2 = factory.create_administration_area(
            name='San Ma Muang',
            authority=self.authority_local2,
            contacts=u'0812345d31, 081234532',
            location='0101000020E6100000747DFEFFE8CA5840F88CC02F60D73340',
            mpoly='0106000020E61000000100000001030000000100000008000000CBEAD1491CCA584049191BFF15D53340D7A88BA915CA584061084E9C65D93340FB0B0BCF35CA58407BEB75947DDB3340E9C77CC729CB5840D22E947EF7D83340BB159EBD23CB58402501C2E41BD73340F7C5624AC5CA5840424BB0129DD53340A9EDDCF76CCA584004B7FE133BD53340CBEAD1491CCA584049191BFF15D53340'
        )
        self.area_yellow3  = factory.create_administration_area(
            name='San Din Daeng',
            authority=self.authority_local1,
            contacts=u'081234541',
            location='0101000020E6100000E54E02FE1DCB5840C70CD8FE63D43340',
            mpoly='0106000020E610000001000000010300000001000000060000000F1427E78CCB584021A9A9340DD33340A9EDDCF76CCA584004B7FE133BD53340F7C5624AC5CA5840424BB0129DD53340D433AA18A4CB5840543ADFF0E6D43340DBF7325C9BCB584064255A1334D333400F1427E78CCB584021A9A9340DD33340'
        )
        self.area_yellow4  = factory.create_administration_area(
            name='Thi',
            authority=self.authority_local2,
            contacts=u'081234551',
            location='0101000020E61000005F48E24023CC58402DDBDA0410D43340',
            mpoly='0106000020E6100000010000000103000000010000000900000029545F57A7CC584057B5A5C2BDD133402AF150FC22CC5840C6D2FD8601D23340DBF7325C9BCB584064255A1334D33340D433AA18A4CB5840543ADFF0E6D4334033C777F4BECB5840F19BE50EA2D5334094C547082DCC5840A587959543D73340ECA4542CFBCC5840400A8DFE4ED433403352E6B804CD5840E40AD728F2D3334029545F57A7CC584057B5A5C2BDD13340'
        )
        self.area_green1  = factory.create_administration_area(
            name='Nong Hang',
            authority=self.authority_local2,
            contacts=u'081234561',
            location='0101000020E6100000A5807A54F8CC584076D3B9E4B0D73340',
            mpoly='0106000020E61000000100000001030000000100000007000000ECA4542CFBCC5840400A8DFE4ED4334094C547082DCC5840A587959543D733405E3B0A2927CC5840B06F4B81B1D83340366BE19F3ECC5840D1F2A6CE7DD93340C716DEF454CC5840070F20D6FAD9334048ACD40656CD584063CBDD3472D73340ECA4542CFBCC5840400A8DFE4ED43340'
        )
        self.area_green2  = factory.create_administration_area(
            name='Nong Yao',
            authority=self.authority_local2,
            contacts=u'081234571',
            location='0101000020E6100000FAC18E396ECB58407A60321B85DA3340',
            mpoly='0106000020E610000001000000010300000001000000070000005E3B0A2927CC5840B06F4B81B1D83340E9C77CC729CB5840D22E947EF7D83340FB0B0BCF35CA58407BEB75947DDB3340FC90AC1D31CA5840E6C52C42F7DB334097E9098235CA5840892C1BD2E4DD3340366BE19F3ECC5840D1F2A6CE7DD933405E3B0A2927CC5840B06F4B81B1D83340'
        )
        self.area_green3  = factory.create_administration_area(
            name='Mai San Pa Daeng',
            authority=self.authority_local2,
            contacts=u'081234581',
            location='0101000020E61000008D81AFC748C95840C00DCE3338D73340',
            mpoly='0106000020E61000000100000001030000000100000005000000FB5E00E207CA584056F474507AD43340025D582C49C858401D44D693DED63340D7A88BA915CA584061084E9C65D93340CBEAD1491CCA584049191BFF15D53340FB5E00E207CA584056F474507AD43340'
        )
        self.area_green4  = factory.create_administration_area(
            name='Nikhom Phet Phaithun',
            authority=self.authority_local2,
            contacts=u'081234591',
            location='0101000020E61000001DCCE4A31EC958402919E70C18D93340',
            mpoly='0106000020E61000000100000001030000000100000006000000025D582C49C858401D44D693DED633404CF191215DC75840B663CE052AD73340FC90AC1D31CA5840E6C52C42F7DB3340FB0B0BCF35CA58407BEB75947DDB3340D7A88BA915CA584061084E9C65D93340025D582C49C858401D44D693DED63340'
        )
        self.area_green5  = factory.create_administration_area(
            name='Mae Sun Luang',
            authority=self.authority_local2,
            contacts=u'081234601',
            location='0101000020E61000006FFA2FE704CB5840BA705ACF94D33340',
            mpoly='0106000020E610000001000000010300000001000000070000005E48DB6B10CB5840F7FE9FFC0DD133403B18E6B9FBC958402DBC29F8C6D13340FB5E00E207CA584056F474507AD43340CBEAD1491CCA584049191BFF15D53340A9EDDCF76CCA584004B7FE133BD533400F1427E78CCB584021A9A9340DD333405E48DB6B10CB5840F7FE9FFC0DD13340'
        )
        self.area_green6  = factory.create_administration_area(
            name='Pong Nok',
            authority=self.authority_local2,
            #contacts=u'081234611',
            location='0101000020E6100000B43F2F60B2CB58400E4DFAF7F0D03340',
            mpoly='0106000020E610000001000000010300000001000000060000006AA6CF8179CB5840D075774672CE33405E48DB6B10CB5840F7FE9FFC0DD133400F1427E78CCB584021A9A9340DD33340DBF7325C9BCB584064255A1334D333402AF150FC22CC5840C6D2FD8601D233406AA6CF8179CB5840D075774672CE3340'
        )
        self.area_ignore1  = factory.create_administration_area(
            name='Mae Kha',
            authority=self.authority_local1,
            contacts=u'081234621',
            location='0101000020E61000008EA70E871FCD58405C300274A9D83340',
            mpoly='0106000020E6100000010000000103000000010000000500000048ACD40656CD584063CBDD3472D73340C716DEF454CC5840070F20D6FAD933407E251B3C8BCC5840FC23C4D3B9DB33401285101DACCD5840B6AD7046B2D8334048ACD40656CD584063CBDD3472D73340'
        )
        self.area_ignore2  = factory.create_administration_area(
            name='Nong Buak Chang',
            authority=self.authority_local2,
            contacts=u'081234631',
            location='0101000020E610000019413AA79FCD5840763DEA1282D63340',
            mpoly='0106000020E6100000010000000103000000010000000800000017A4B18F0DCE584008E26AE445D333403352E6B804CD5840E40AD728F2D33340ECA4542CFBCC5840400A8DFE4ED4334048ACD40656CD584063CBDD3472D733401285101DACCD5840B6AD7046B2D8334091A0759DBECD5840DFD32CDCBCD83340FE8F84351ACE5840BC201FA951D3334017A4B18F0DCE584008E26AE445D33340'
        )
        self.area_ignore3  = factory.create_administration_area(
            name='Rai',
            authority=self.authority_local2,
            contacts=u'081234641',
            location='0101000020E610000000F4A8B663CD584051BE03B0BFD03340',
            mpoly='0106000020E610000001000000010300000001000000050000007CBCBE53EFCC584033ABD1AC46C9334029545F57A7CC584057B5A5C2BDD133403352E6B804CD5840E40AD728F2D3334017A4B18F0DCE584008E26AE445D333407CBCBE53EFCC584033ABD1AC46C93340'
        )


        self.notification_template_red = NotificationTemplate.objects.create(
            condition="plan.code == '%s'" % self.plan.code,
            template="red plan",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_red.enable(self.authority_livestock, to="@[plan:red]")

        self.notification_template_yellow = NotificationTemplate.objects.create(
            condition="plan.code == '%s'" % self.plan.code,
            template="yellow plan",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_yellow.enable(self.authority_livestock, to="@[plan:yellow]")

        self.notification_template_green = NotificationTemplate.objects.create(
            condition="plan.code == '%s'" % self.plan.code,
            template="green plan",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_green.enable(self.authority_livestock, to="@[plan:green]")


    def test_plan_areas(self):


        # Check rewrite tel from unknown user input
        self.assertEqual(self.area_yellow1.get_contacts(), ['081234521', '081234522', '081234523'])


        # No outbreak no notification
        report1 = factory.create_report(
            type=self.report_type,
            administration_area=self.area_red1,
            form_data={}
        )
        report1.state = self.state_case
        report1.save()

        self.assertEqual(PlanReport.objects.filter(plan=self.plan, report=report1).count(), 0)


        # Check missing condition, not send notification
        report2 = factory.create_report(
            type=self.report_type_ignore,
            administration_area=self.area_red1,
            form_data={}
        )
        report2.state = self.state_outbreak_ignore
        report2.save()
        self.assertEqual(PlanReport.objects.filter(plan=self.plan, report=report2).count(), 0)

        level_areas = self.plan.level_areas(self.area_red1)

        self.assertIn(self.area_red1, level_areas['red'])
        self.assertIn(self.area_yellow1, level_areas['yellow'])
        self.assertIn(self.area_yellow2, level_areas['yellow'])
        self.assertIn(self.area_yellow3, level_areas['yellow'])
        self.assertIn(self.area_yellow4, level_areas['yellow'])
        self.assertIn(self.area_green1, level_areas['green'])
        self.assertIn(self.area_green2, level_areas['green'])
        self.assertIn(self.area_green3, level_areas['green'])
        self.assertIn(self.area_green4, level_areas['green'])
        self.assertIn(self.area_green5, level_areas['green'])
        self.assertIn(self.area_green6, level_areas['green'])
        self.assertNotIn(self.area_ignore1, level_areas['red'])
        self.assertNotIn(self.area_ignore2, level_areas['red'])
        self.assertNotIn(self.area_ignore3, level_areas['red'])
        self.assertNotIn(self.area_ignore1, level_areas['yellow'])
        self.assertNotIn(self.area_ignore2, level_areas['yellow'])
        self.assertNotIn(self.area_ignore3, level_areas['yellow'])
        self.assertNotIn(self.area_ignore1, level_areas['green'])
        self.assertNotIn(self.area_ignore2, level_areas['green'])
        self.assertNotIn(self.area_ignore3, level_areas['green'])


        for level, areas in level_areas.iteritems():
            for area in areas:
                for contact in area.get_contacts():
                    self.assertEqual(Notification.objects.filter(to=contact).count(), 0)


        # When outbreak, system will send notification to contacts areas
        report1.state = self.state_outbreak
        report1.save()



        plan_report = PlanReport.objects.filter(plan=self.plan, report=report1).latest('id')
        plan_report_log = json.loads(plan_report.log)
        self.assertEqual(plan_report_log['plan']['id'], 1)
        self.assertEqual(plan_report_log['level_areas'], self.plan.dict_level_areas(self.area_red1))
        self.assertIn('[plan-report:%d]' % plan_report.id, ReportComment.objects.filter(report=report1).order_by('-id')[0].message)



        for level, areas in level_areas.iteritems():
            for area in areas:
                for contact in area.get_contacts():
                    query_set = Notification.objects.filter(to=contact).order_by('-id')
                    self.assertEqual(query_set.count(), 1)
                    self.assertEqual(query_set[0].render_message('sms'), '%s plan' % level)


        # Cross check notification
        self.notification_template_outbreak = NotificationTemplate.objects.create(
            condition="report.type.code == '%s' and report.state_code == '%s'" % (self.report_type.code, self.state_outbreak.code),
            template="outbreak notification template",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_outbreak.enable(self.authority_livestock, to="0891234560")

        report3 = factory.create_report(
            type=self.report_type,
            administration_area=self.area_red1,
            form_data={}
        )
        report3.state = self.state_outbreak
        report3.save()

        for level, areas in level_areas.iteritems():
            for area in areas:
                for contact in area.get_contacts():
                    query_set = Notification.objects.filter(to=contact).order_by('-id')
                    self.assertEqual(query_set.count(), 2)
                    self.assertEqual(query_set[0].render_message('sms'), '%s plan' % level)

        self.assertEqual(Notification.objects.filter(to='0891234560').order_by('-id').count(), 1)


        # Resend notification
        plan_report.notify(self.area_red1)

        for level, areas in level_areas.iteritems():
            for area in areas:
                for contact in area.get_contacts():
                    query_set = Notification.objects.filter(to=contact).order_by('-id')
                    if contact in self.area_red1.get_contacts():
                        self.assertEqual(query_set.count(), 3)
                    else:
                        self.assertEqual(query_set.count(), 2)

                    self.assertEqual(query_set[0].render_message('sms'), '%s plan' % level)


        plan_report.notify(self.area_red1)
        plan_report.notify(self.area_yellow1)

        for level, areas in level_areas.iteritems():
            for area in areas:
                for contact in area.get_contacts():
                    query_set = Notification.objects.filter(to=contact).order_by('-id')
                    if contact in self.area_red1.get_contacts():
                        self.assertEqual(query_set.count(), 4)
                    elif contact in self.area_yellow1.get_contacts():
                        self.assertEqual(query_set.count(), 3)
                    else:
                        self.assertEqual(query_set.count(), 2)

                    self.assertEqual(query_set[0].render_message('sms'), '%s plan' % level)


        # test send notification level areas to local goverment

        self.notification_template_authority_red = NotificationTemplate.objects.create(
            condition="plan.code == '%s' and report.accepted_authority_plan_level(authority, '%s', 'red')" % (self.plan.code, self.plan.code),
            template="red plan authority {% plan_authority_level_areas plan authority 'red' %}",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_REPORT
        )
        reuse_enable_local1 = self.notification_template_authority_red.enable(self.authority_local1, to="0888888881, 0888888882")
        reuse_enable_local2 = self.notification_template_authority_red.enable(self.authority_local2, to="0878888881, 0878888882")

        self.notification_template_authority_yellow = NotificationTemplate.objects.create(
            condition="plan.code == '%s' and report.accepted_authority_plan_level(authority, '%s', 'yellow')" % (self.plan.code, self.plan.code),
            template="yellow plan authority {% plan_authority_level_areas plan authority 'yellow' %}",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_REPORT
        )
        self.notification_template_authority_yellow.enable(self.authority_local1, to="@[template:%s]" % reuse_enable_local1.template.id)
        self.notification_template_authority_yellow.enable(self.authority_local2, to="@[template:%s]" % reuse_enable_local2.template.id)

        self.notification_template_authority_green = NotificationTemplate.objects.create(
            condition="plan.code == '%s' and report.accepted_authority_plan_level(authority, '%s', 'green')" % (self.plan.code, self.plan.code),
            template="green plan authority {% plan_authority_level_areas plan authority 'green' %}",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_REPORT
        )
        self.notification_template_authority_green.enable(self.authority_local1, to="@[template:%s]" % reuse_enable_local1.template.id)
        self.notification_template_authority_green.enable(self.authority_local2, to="@[template:%s]" % reuse_enable_local2.template.id)

        report4 = factory.create_report(
            type=self.report_type,
            administration_area=self.area_red1,
            form_data={}
        )
        report4.state = self.state_outbreak
        report4.save()


        for level, areas in level_areas.iteritems():
            for area in areas:
                for contact in area.get_contacts():
                    query_set = Notification.objects.filter(to=contact).order_by('-id')
                    if contact in self.area_red1.get_contacts():
                        self.assertEqual(query_set.count(), 5)
                    elif contact in self.area_yellow1.get_contacts():
                        self.assertEqual(query_set.count(), 4)
                    else:
                        self.assertEqual(query_set.count(), 3)

                    self.assertEqual(query_set[0].render_message('sms'), '%s plan' % level)


        # Local goverment 1
        self.assertEqual(Notification.objects.filter(to='0888888881').order_by('id').count(), 2)
        self.assertEqual(Notification.objects.filter(to='0888888881').order_by('id')[0].render_message('sms'), 'red plan authority %s' % (self.area_red1.address))
        self.assertEqual(Notification.objects.filter(to='0888888881').order_by('id')[1].render_message('sms'), 'yellow plan authority %s, %s' % (self.area_yellow1.address, self.area_yellow3.address))

        self.assertEqual(Notification.objects.filter(to='0888888882').order_by('id').count(), 2)
        self.assertEqual(Notification.objects.filter(to='0888888882').order_by('id')[0].render_message('sms'), 'red plan authority %s' % (self.area_red1.address))
        self.assertEqual(Notification.objects.filter(to='0888888882').order_by('id')[1].render_message('sms'), 'yellow plan authority %s, %s' % (self.area_yellow1.address, self.area_yellow3.address))

        # Local goverment 2
        self.assertEqual(Notification.objects.filter(to='0878888881').order_by('id').count(), 2)
        self.assertEqual(Notification.objects.filter(to='0878888881').order_by('id')[0].render_message('sms'), 'yellow plan authority %s, %s' % (self.area_yellow2.address, self.area_yellow4.address))
        self.assertEqual(Notification.objects.filter(to='0878888881').order_by('id')[1].render_message('sms'), 'green plan authority %s, %s, %s, %s, %s, %s' % (
            self.area_green1.address, self.area_green2.address, self.area_green3.address, self.area_green4.address, self.area_green5.address, self.area_green6.address
        ))

        self.assertEqual(Notification.objects.filter(to='0878888882').order_by('id').count(), 2)
        self.assertEqual(Notification.objects.filter(to='0878888882').order_by('id')[0].render_message('sms'), 'yellow plan authority %s, %s' % (self.area_yellow2.address, self.area_yellow4.address))
        self.assertEqual(Notification.objects.filter(to='0878888882').order_by('id')[1].render_message('sms'), 'green plan authority %s, %s, %s, %s, %s, %s' % (
            self.area_green1.address, self.area_green2.address, self.area_green3.address, self.area_green4.address, self.area_green5.address, self.area_green6.address
        ))

        # test send notification to difference context (headman, volunteer)

        # Headman
        self.notification_template_red_headman = NotificationTemplate.objects.create(
            condition="plan.code == '%s'" % self.plan.code,
            template="red plan headman",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_red_headman.enable(self.authority_livestock, to="@[plan:red:headman]")

        self.notification_template_yellow_headman = NotificationTemplate.objects.create(
            condition="plan.code == '%s'" % self.plan.code,
            template="yellow plan headman",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_yellow_headman.enable(self.authority_livestock, to="@[plan:yellow:headman]")

        self.notification_template_green_headman = NotificationTemplate.objects.create(
            condition="plan.code == '%s'" % self.plan.code,
            template="green plan headman",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_green_headman.enable(self.authority_livestock, to="@[plan:green:headman]")


        # Volunteer
        self.notification_template_red_volunteer = NotificationTemplate.objects.create(
            condition="plan.code == '%s'" % self.plan.code,
            template="red plan volunteer",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_red_volunteer.enable(self.authority_livestock, to="@[plan:red:volunteer]")

        self.notification_template_yellow_volunteer = NotificationTemplate.objects.create(
            condition="plan.code == '%s'" % self.plan.code,
            template="yellow plan volunteer",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_yellow_volunteer.enable(self.authority_livestock, to="@[plan:yellow:volunteer]")

        self.notification_template_green_volunteer = NotificationTemplate.objects.create(
            condition="plan.code == '%s'" % self.plan.code,
            template="green plan volunteer",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_green_volunteer.enable(self.authority_livestock, to="@[plan:green:volunteer]")


        report5 = factory.create_report(
            type=self.report_type,
            administration_area=self.area_red1,
            form_data={}
        )
        report5.state = self.state_outbreak
        report5.save()

        for level, areas in level_areas.iteritems():
            for area in areas:
                for contact in area.get_contacts():
                    query_set = Notification.objects.filter(to=contact).order_by('-id')

                    if contact in ['081234510']:
                        self.assertEqual(query_set.count(), 7)
                    elif contact in ['081234521', '081234522', '081234523']:
                        self.assertEqual(query_set.count(), 6)

                    else:

                        if contact in self.area_red1.get_contacts():
                            self.assertEqual(query_set.count(), 6)
                        elif contact in self.area_yellow1.get_contacts():
                            self.assertEqual(query_set.count(), 5)
                        else:
                            self.assertEqual(query_set.count(), 4)

                        self.assertEqual(query_set[0].render_message('sms'), '%s plan' % level)

        self.notification_template_state_suspect_outbreak_headman = NotificationTemplate.objects.create(
            condition="report.type.code == '%s' and report.state_code == '%s'" % (self.report_type.code, self.state_suspect_outbreak.code),
            template="suspect outbreak notification template headman",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_state_suspect_outbreak_headman.enable(self.authority_livestock, to="@[contacts:headman]")

        self.notification_template_state_suspect_outbreak_volunteer = NotificationTemplate.objects.create(
            condition="report.type.code == '%s' and report.state_code == '%s'" % (self.report_type.code, self.state_suspect_outbreak.code),
            template="suspect outbreak notification template volunteer",
            authority=self.authority_livestock,
            type=NotificationTemplate.TYPE_PRIVATE
        )
        self.notification_template_state_suspect_outbreak_volunteer.enable(self.authority_livestock, to="@[contacts:volunteer]")

        report6 = factory.create_report(
            type=self.report_type,
            administration_area=self.area_yellow1,
            form_data={}
        )
        report6.state = self.state_suspect_outbreak
        report6.save()

        for level, areas in level_areas.iteritems():
            for area in areas:
                for contact in area.get_contacts():
                    query_set = Notification.objects.filter(to=contact).order_by('-id')

                    if contact in ['081234510']:
                        self.assertEqual(query_set.count(), 7)
                    elif contact in ['081234521', '081234522', '081234523']:
                        self.assertEqual(query_set.count(), 7)
                        self.assertEqual(Notification.objects.filter(to='081234521').order_by('-id')[0].render_message('sms'), 'suspect outbreak notification template headman')
                        self.assertEqual(Notification.objects.filter(to='081234522').order_by('-id')[0].render_message('sms'), 'suspect outbreak notification template volunteer')
                        self.assertEqual(Notification.objects.filter(to='081234523').order_by('-id')[0].render_message('sms'), 'suspect outbreak notification template volunteer')

                    else:

                        if contact in self.area_red1.get_contacts():
                            self.assertEqual(query_set.count(), 6)
                        elif contact in self.area_yellow1.get_contacts():
                            self.assertEqual(query_set.count(), 5)
                        else:
                            self.assertEqual(query_set.count(), 4)

                        self.assertEqual(query_set[0].render_message('sms'), '%s plan' % level)
