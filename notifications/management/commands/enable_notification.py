# -*- encoding: utf-8 -*-
from optparse import make_option

from django.core.management import BaseCommand, CommandError

from notifications.models import NotificationTemplate, NotificationAuthority
from common.models import Domain


class Command(BaseCommand):

    help = 'create notification_authority <ref_no ref_no ...>'
    option_list = BaseCommand.option_list + (
        make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Whether to force mode, default is dry_run mode'
        ),
        make_option(
            '--domain',
            type='int',
            action='store',
            dest='domain_id',
            default=None,
            help='Specify domain id'
        ),
        make_option(
            '--from-template',
            type='int',
            action='store',
            dest='template_id',
            default=None,
            help='Specify template id'
        ),
    )

    def handle(self, *args, **options):
        dry_run = not options['force']
        domain_id = options['domain_id']
        template_id = options['template_id']
        ref_nos = list(args[0:])

        if template_id:
            template = NotificationTemplate.objects.get(pk=template_id)
            self.process(template, dry_run)
        else:
            domain = Domain.objects.get(pk=domain_id)
            templates = NotificationTemplate.objects.filter(domain=domain)
            if ref_nos:
                templates = templates.filter(ref_no__in=ref_nos)
            for template in templates:
                self.process(template, dry_run)

    @staticmethod
    def process(template, dry_run):

        root_authority = template.authority
        pass_authority_ids = set([])

        def enable(authority):
            if authority.id in pass_authority_ids:
                return
            pass_authority_ids.add(authority.id)

            try:
                NotificationAuthority.objects.get(template=template, authority=authority)
            except NotificationAuthority.DoesNotExist:
                if not dry_run:
                    NotificationAuthority.objects.create(template=template, authority=authority, domain=template.domain)
                else:
                    print('create NotificationAuthority template %s on authority %s, domain %s' % (template, authority, template.domain))

            for child in authority.authority_inherits.all():
                enable(child)

        enable(root_authority)
