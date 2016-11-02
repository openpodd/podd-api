# -*- encoding: utf-8 -*-
from django.conf import settings

from django.core.management import BaseCommand
from accounts.models import Authority
from notifications.models import NotificationTemplate
from reports.models import ReportType


class Command(BaseCommand):

    help = 'Update notification template case report'

    def handle(self, *args, **options):

        settings.CURRENT_DOMAIN_ID = 1
        cnx = Authority.objects.get(id=120)
        lgvs = cnx.get_children_all()

        for t in NotificationTemplate.objects.all():
            t.description = t.description.replace(u'สัตว์ป่วยตาย', u'สัตว์ป่วย/ตาย')
            t.save()

        for t in NotificationTemplate.objects.filter(authority__in=[82, 83], description__startswith='REPORT'):
            description = t.description.replace(u'แจ้งทีมสาธารณสุขจังหวัดเชียงใหม่', u'แจ้ง อปท')
            print t
            try:
                tt = NotificationTemplate.objects.get(description=description)
            except NotificationTemplate.DoesNotExist:
                tt = NotificationTemplate.objects.create(
                    type=NotificationTemplate.TYPE_PRIVATE,
                    template=t.template,
                    condition=t.condition,
                    authority=t.authority,
                    description=description,
                )
                print 'Create %s' % tt
            tt.enable(t.authority)
            for lgv_id in lgvs:
                tt.enable(Authority.objects.get(id=lgv_id))

        authority = Authority.objects.get(id=83)

        report_type = ReportType.objects.get(id=1)
        description = u'REPORT: %s: แจ้ง อปท' % report_type.name
        try:
            tt = NotificationTemplate.objects.get(description=description)
        except NotificationTemplate.DoesNotExist:
            tt = NotificationTemplate.objects.create(
                type=NotificationTemplate.TYPE_PRIVATE,
                template=t.template,
                condition=u"report.type.code == '%s'" % report_type.code,
                authority=authority,
                description=description,
            )
            print 'Create %s' % tt
        tt.enable(authority)
        print tt, 'ccccc'
        for lgv_id in lgvs:
            tt.enable(Authority.objects.get(id=lgv_id))

        report_type = ReportType.objects.get(id=2)
        description = u'REPORT: %s: แจ้ง อปท' % report_type.name
        try:
            tt = NotificationTemplate.objects.get(description=description)
        except NotificationTemplate.DoesNotExist:
            tt = NotificationTemplate.objects.create(
                type=NotificationTemplate.TYPE_PRIVATE,
                template=t.template,
                condition=u"report.type.code == '%s'" % report_type.code,
                authority=authority,
                description=description,
            )
            print 'Create %s' % tt
        tt.enable(authority)
        for lgv_id in lgvs:
            tt.enable(Authority.objects.get(id=lgv_id))
