# -*- encoding: utf-8 -*-

import json

from django.core.management import BaseCommand
from django.template import Template, Context
from reports.models import Report, ReportType


class Command(BaseCommand):

    help = 'Update public report data'

    def handle(self, *args, **options):

        report_type = ReportType.objects.get(id=24)
        report_type.django_template = u'{% if foodSuspect %}สงสัย{{ foodSuspect }}{% endif %}{% if address %}<br/>ที่{{ address }}{% elif location %}<br/>ที่{{ location }}{% endif %}'
        report_type.save()

        report_type = ReportType.objects.get(id=26)
        report_type.django_template = u'{% if suspect %}สงสัยว่าปนเปื้อน{{ suspect }}{% endif %}{% if address %}<br/>ที่{{ address }}{% elif location %}<br/>ที่{{ location }}{% endif %}'
        report_type.save()

        report_type = ReportType.objects.get(id=27)
        report_type.django_template = u'{% if typeOther %}ประเภท{{ typeOther }}{% else %}ประเภท{{ type }}{% endif %} {% if address %}<br/>ที่{{ address }}{% elif location %}<br/>ที่{{ location }}{% endif %}'
        report_type.save()

        report_type = ReportType.objects.get(id=33)
        report_type.django_template = u'{% if animalType %}ชนิดสัตว์คือ{{ animalType }}{% endif %}{% if sickCount %}  <br/>ป่วยจำนวน {{ sickCount }} ตัว{% endif %}{% if deathCount %}  <br/>ตายจำนวน {{ deathCount }} ตัว{% endif %}{% if address %}  <br/>ที่{{ address }}{% elif location %}  <br/>ที่{{ location }}{% endif %}'
        report_type.save()

        report_type = ReportType.objects.get(id=32)
        report_type.django_template = u'{% if animalType or animalTypeOther %}ชนิดสัตว์คือ {% endif %}{% if animalTypeOther %}{{ animalTypeOther }}{% elif animalType %}{{ animalType }}{% endif %}{% if animalStatus %} <br/>ซึ่ง{{ animalStatus }}{% endif %}{% if symptom %} <br/>โดยแสดงอาการ{{ symptom }}{% else %} <br/>โดยไม่แสดงอาการพิษสุนัขบ้า{% endif %}{% if address %}<br/>ที่{{ address }}{% elif location %}<br/>ที่{{ location }}{% endif %}'
        report_type.save()

        reports = Report.objects.filter(is_public=True)
        for obj in reports:
            template = obj.type.django_template
            form_data = json.loads(obj.form_data)
            t = Template(template)
            c = Context(form_data)
            text = t.render(c)
            if text.startswith('<br/>'):
                text = text[5:]
            obj.rendered_form_data = text
            obj.rendered_original_form_data = obj.rendered_form_data
            obj.save()