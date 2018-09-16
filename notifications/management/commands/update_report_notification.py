# coding=utf-8
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from optparse import make_option

import json
from django.core.management import BaseCommand

from common.models import Domain
from notifications.models import NotificationTemplate, NotificationAuthority
from reports.models import ReportType, ReportState


class Command(BaseCommand):
    args = '<domain> <filename>'
    help = u'''
update notification from specification file
file example.
[
  {
    "reportTypeCode": "10868f6e-c3ad-11e4-b",
    "states": {
      "report": {
        "messages": [
          {
            "message": "รายงานของท่านเข้าข่ายปัญหาอาหารปลอดภัย กรุณารอการติดต่อกลับจากเจ้าหน้าที่",
            "type": "reporter",
          },
          {
            "message": "มีรายงานปัญหาอาหารปลอดภัย ประเภท {{ report.topic }} โดย {{report.created_by.name}} พื้นที่  {{report.administration_area.name}} ติดต่อกลับที่ {{report.created_by.telephone}}",
            "type": "report",
            "to": "อปท. รพสต."
          },
          {
            "message": "มีรายงานปัญหาอาหารปลอดภัย ประเภท {{ report.topic }} โดย {{report.created_by.name}} พื้นที่  {{report.administration_area.name}} ข้อมูลเพิ่มเติมที่ ",
            "type": "report",
            "to": "สสจ. สสอ."
          }
        ]        
      },
      "false-report": {
        "messages": [
          {
            "message": "รายงานของท่านได้รับการตรวจสอบแล้ว พบว่าไม่เข้าข่ายปัญหาที่ส่งผลต่อผู้บริโภค ขอบคุณที่ร่วมกันทำงานเพื่อชุมชนของเรา",
            "type": "reporter",
          },
          {
            "message": "รายงานอาหารปลอดภัย ประเภท {{ report.topic }} โดย พื้นที่  {{report.administration_area.name}} ได้รับการตรวจสอบแล้วไม่ส่งผลกระทบต่อชุมชน",
            "type": "report",
            "to": "อปท. รพสต. สสจ. สสอ."
          }
        ]        
      },
      "case": {
        "messages": [
          {
            "message": "รายงานของท่านได้รับการตรวจสอบแล้ว เจ้าหน้าที่กำลังดำเนินการตามแผน",
            "type": "reporter",
          },
          {
            "message": "รายงานอาหารปลอดภัย ประเภท {{ report.topic }} โดย พื้นที่  {{report.administration_area.name}} กำลังดำเนินการแก้ไขตามแผน",
            "type": "report",
            "to": "อปท. รพสต."
          },
          {
            "message": "รายงานอาหารปลอดภัย ประเภท {{ report.topic }} โดย พื้นที่  {{report.administration_area.name}} กำลังดำเนินการแก้ไขตามแผน จากหน่วยงานในพื้นที่",
            "type": "report",
            "to": "สสจ. สสอ."
          }
        ]        
      },
      "finish": {
        "messages": [
          {
            "message": "รายงานของท่านได้รับการตอบสนองเป็นที่เรียบร้อยแล้ว ขอบคุณที่ร่วมกันทำงานเพื่อชุมชนของเรา",
            "type": "reporter",
          },
          {
            "message": "รายงานอาหารปลอดภัย ประเภท {{ report.topic }} โดย พื้นที่  {{report.administration_area.name}} ได้รับการแก้ไขเรียบร้อยแล้ว",
            "type": "report",
            "to": "อปท. รพสต. สสจ. สสอ."
          }
        ]        
      },
    }
  }

]
    '''
    option_list = BaseCommand.option_list + (
        make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Whether to force mode, default is dry_run mode'
        ),
    )

    def _get_state(self, code, report_type):
        report_states = ReportState.objects.filter(code=code, domain=self.domain, report_type=report_type)
        if len(report_states) > 0:
            return report_states[0]
        else:
            return None

    @staticmethod
    def _gen_template(message):
        return u'''
{
    "default": {
        "body": "%s", 
        "subject": "{{ report.rendered_report_subject }}"
    }
}        
        ''' % (message,)

    def upsert_notification_template(self, upd_noti_template):
        pass_authority_ids = set([])
        def enable(authority, template):
            if authority.id in pass_authority_ids:
                return
            pass_authority_ids.add(authority.id)

            try:
                NotificationAuthority.objects.get(template=template, authority=authority)
            except NotificationAuthority.DoesNotExist:
                NotificationAuthority.objects.create(template=template, authority=authority, domain=template.domain)

            for child in authority.authority_inherits.all():
                enable(child, template)

        templates = NotificationTemplate.objects.filter(
            domain = upd_noti_template.domain,
            description = upd_noti_template.description,
            authority = upd_noti_template.authority,
        ).all()
        if len(templates) > 0:
            orig_noti_template = templates[0]
            orig_noti_template.template = upd_noti_template.template
            orig_noti_template.condition = upd_noti_template.condition
            self._print_noti(orig_noti_template, "update")
            if not self.dry_run:
                orig_noti_template.save()
        else:
            self._print_noti(upd_noti_template, "create")
            if not self.dry_run:
                upd_noti_template.save()
                enable(upd_noti_template.authority, upd_noti_template)


    def _print_noti(self, noti, action):
        print("------------------------------------------")
        print("%s notificationTemplate with" % (action,))
        if noti.id:
            print("id = %d" % (noti.id,))
        print("condition = %s" % (noti.condition,))
        print("template = %s" % (noti.template,))
        print("description = %s" % (noti.description,))
        print("type = %s" % (noti.type))

    def handle(self, *args, **options):
        if len(args) != 2:
            print('usage: ./manage.py update_report_notification domain_id filename')
            exit(0)

        self.dry_run = not options['force']

        self.domain = Domain.objects.get(id=args[0])
        filename = args[1]
        save_list = []
        with open(filename, 'r') as f:
            notifications = json.load(f)
            for noti_group in notifications:
                code = noti_group['reportTypeCode']
                report_type = ReportType.objects.filter(code=code, domain=self.domain)[0]
                if report_type:
                    for state_code, state in noti_group['states'].iteritems():
                        report_state = self._get_state(state_code, report_type)
                        if report_state:
                            for noti_msg in state['messages']:
                                template = NotificationTemplate()
                                template.authority = report_type.authority
                                template.domain = self.domain
                                noti_msg_type = noti_msg['type']

                                if noti_msg_type == 'reporter':
                                    template.type = NotificationTemplate.TYPE_REPORTER_FEEDBACK
                                    send_to = u"อาสา"
                                elif noti_msg_type == 'report':
                                    template.type = NotificationTemplate.TYPE_REPORT
                                    send_to = noti_msg['to'] if 'to' in noti_msg else noti_group['default_report_to']
                                else:
                                    print("notification type not match, %s" % (noti_msg_type,))
                                template.condition = "report.type.code == '%s' and report.state.code == '%s' and report.parent is None" %\
                                                    (report_type.code, report_state.code)
                                template.template = self._gen_template(noti_msg['message'])
                                if 'description' in noti_msg:
                                    template.description = noti_msg['description']
                                else:
                                    template.description = u'%s: %s: แจ้ง %s' % (report_state.name , report_type.name, send_to)
                                save_list.append(template)
                        else:
                            print ("no report state found for state:%s, reportType:%s" % (state_code, code))
                else:
                    print("no report type found for %s" % (code,))

        for item in save_list:
            self.upsert_notification_template(item)
