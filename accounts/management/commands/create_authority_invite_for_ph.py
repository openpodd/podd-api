# -*- encoding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Authority, AuthorityInvite
from common.constants import USER_STATUS_PUBLIC_HEALTH
from common.functions import get_data_from_csv
from reports.models import AdministrationArea


class Command(BaseCommand):
    args = 'domain_id'
    help = 'create invitation code for public health authority.'

    def handle(self, *args, **options):

        if not args:
            raise CommandError('Please provide domain_id')

        domain_id = args[0]
        settings.CURRENT_DOMAIN_ID = domain_id

        # first pass
        for authority in Authority.objects.filter(domain_id=domain_id):
            if not AuthorityInvite.objects.filter(status=USER_STATUS_PUBLIC_HEALTH, authority=authority, disabled=False).exists():
                print 'create invite for %s' % (authority.code,)
                ph_invite = AuthorityInvite(
                    authority=authority,
                    status=USER_STATUS_PUBLIC_HEALTH
                )
                ph_invite.save()
