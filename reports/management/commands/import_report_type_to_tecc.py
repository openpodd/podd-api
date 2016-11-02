# -*- encoding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from common.models import Domain
from reports.models import ReportType, ReportState


class Command(BaseCommand):
    help = 'Move Users from Elephant to TECC'

    def handle(self, *args, **options):

        try:
            elephant = Domain.objects.get(code='Elephant')
        except Domain.DoesNotExist:
            raise CommandError('No Domain Elephant')

        report_types = ReportType.objects.filter(domain=elephant)

        try:
            tecc = Domain.objects.get(code='TECC')
        except Domain.DoesNotExist:
            raise CommandError('No Domain TECC')

        settings.CURRENT_DOMAIN_ID = tecc.id
        
        i = 0
        for report_type in report_types:
            try:
                ReportType.objects.get(code='tecc-%s' % report_type.code)
            except ReportType.DoesNotExist:
                report_type.domain_id = tecc.id
                report_type.code = 'tecc-%s' % report_type.code
                report_type.id = None
                report_type.authority = None
                report_type.default_state = None
                report_type.save()
                ReportState.objects.create(report_type=report_type, name='Report', code='report', domain_id=tecc.id)
            i += 1
            print '(', i, '/', report_types.count(), ')', report_type.name

