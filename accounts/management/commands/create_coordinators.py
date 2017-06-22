# -*- encoding: utf-8 -*-
import re
from django.conf import settings

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User, Authority
from common.constants import USER_STATUS_COORDINATOR
from common.factory import randnum
from common.functions import get_data_from_csv


class Command(BaseCommand):
    args = 'authority_code(,) domain_id'
    help = 'Import Users from csv: file_path.csv'

    def handle(self, *args, **options):

        if not args:
            raise CommandError('Please input csv path')

        domain_id = args[1]
        settings.CURRENT_DOMAIN_ID = domain_id

        authority_codes = args[0].split(',')

        for row in authority_codes:
            code = row.replace(" ", "")

            try:
                authority = Authority.objects.get(code=code)
            except Authority.DoesNotExist:
                continue

            match = re.search('\d+', code)
            if match:
                code = match.group(0)

            username = 'podd.%s' % (code)
            password = '%s' % code[-4:]

            user = User.objects.create_user(
                username=username,
                password=password,
                display_password=password,
                first_name=authority.name[:30],
                last_name='',
                status=USER_STATUS_COORDINATOR
            )

            authority.users.add(user)
            authority.admins.add(user)

            print authority.name, ": ",  username
