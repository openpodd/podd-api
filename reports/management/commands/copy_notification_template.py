# -*- encoding: utf-8 -*-
from optparse import make_option

import copy
from django.core.management.base import BaseCommand

from accounts.models import Authority
from common.models import Domain
from notifications.models import NotificationTemplate
from reports.models import ReportType, ReportState, ReportTypeCategory


class Command(BaseCommand):
    args = '<from_domain> <to_domain> <notification_template_id notification_template_id ...>'
    help = 'Copy notification templates'
    option_list = BaseCommand.option_list + (
        make_option(
            '--from-authority',
            action='store',
            dest='from_authority',
            default=None,
            help='Specify origin authority'
        ),
        make_option(
            '--to-authority',
            action='store',
            dest='to_authority',
            default=None,
            help='Specify target authority'
        ),
        make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Whether to force mode, default is dry_run mode'
        ),
    )

    def _copy_notification_templates(self, from_domain, to_domain, from_authority, to_authority, dry_run=True, notification_template_ids=[]):
        if dry_run:
            print ">> DRY RUN <<\n"

        original_notification_templates = NotificationTemplate.objects.filter(domain=from_domain, authority=from_authority)
        if notification_template_ids:
            original_notification_templates = original_notification_templates.filter(id__in=notification_template_ids)

        for original_notification_template in original_notification_templates:
            notification_template = copy.deepcopy(original_notification_template)

            notification_template.pk = None
            notification_template.domain = to_domain
            notification_template.authority = to_authority

            if to_authority:
                notification_template.authority = to_authority
            else:
                notification_template.authority = None

            print "Will copy report notification template from %s to %s using this data:" % (from_domain.name, to_domain.name)
            print " [FROM] id:%s domain:%s authority:%s" % (original_notification_template.pk, original_notification_template.domain, original_notification_template.authority)
            print "   [TO] id:%s domain:%s authority:%s" % (notification_template.pk, notification_template.domain, notification_template.authority)
            if not dry_run:
                notification_template.save()
                print "  - Saved id: %s" % notification_template.pk

            print "---------------------"

    def handle(self, *args, **options):
        from_domain = Domain.objects.get(id=args[0])
        to_domain = Domain.objects.get(id=args[1])
        notification_template_ids = list(args[2:])

        from_authority = options['from_authority']
        if from_authority:
            from_authority = Authority.objects.get(domain=from_domain, id=from_authority)

        to_authority = options['to_authority']
        if to_authority:
            to_authority = Authority.objects.get(domain=to_domain, id=to_authority)

        dry_run = not options['force']

        self._copy_notification_templates(from_domain, to_domain, from_authority, to_authority, dry_run, notification_template_ids)