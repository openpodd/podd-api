# coding=utf-8
from django.core.management import BaseCommand
from common.models import Domain
from notifications.models import NotificationTemplate
from reports.models import ReportType, ReportState
import json
import re

import sys, codecs


class EncodedOut:
    def __init__(self, enc):
        self.enc = enc
        self.stdout = sys.stdout
    def __enter__(self):
        if sys.stdout.encoding is None:
            w = codecs.getwriter(self.enc)
            sys.stdout = w(sys.stdout)
    def __exit__(self, exc_ty, exc_val, tb):
        sys.stdout = self.stdout


class Command(BaseCommand):
    args = '<domain> <reportTypeCode>'
    help = u'''
Dump notification into json file.
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

    def handle(self, *args, **options):
        if len(args) != 2:
            print("usage: ./manage.py dump_report_notification domain_id report_type_code")
            exit(0)

        domain = Domain.objects.get(id=args[0])
        report_type = ReportType.objects.filter(code=args[1], domain=domain).first()
        templates = NotificationTemplate.objects.filter(condition__icontains=report_type.code, domain=domain)
        states = ReportState.objects.filter(report_type=report_type)
        state_map = {}
        for state in states:
            messages = []
            state_map[state.code] = {'messages': messages}
            for template in templates:
                word = "report\.state_code\s*==\s*'%s'" % (state.code,)
                found = re.search(word, template.condition)
                if found:
                    tmp = json.loads(template.template)
                    messages.append({
                        'message': tmp['sms'],
                        'type': template.get_type_display(),
                        'to': template.description,
                        'condition': template.condition,
                        'id': template.id
                    })
        result = {
            'reportTypeCode': report_type.code,
            'states': state_map
        }
        with EncodedOut('utf-8'):
            print(json.dumps(result, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False, encoding='utf8'))
