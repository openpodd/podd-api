# -*- encoding: utf-8 -*-
import time
from django.core.management import BaseCommand
from django.utils.log import getLogger

from accounts.models import User
from common.models import Domain


class Command(BaseCommand):
    help = 'Create default user for cross domain report'

    def handle(self, *args, **options):
        logger = getLogger('management_commands')

        for domain in Domain.objects.all():
            username = 'public-%s' % (domain.id,)
            try:
                user = User.default_manager.get(username=username)
                print((u"user %s for domain %s is already exists" % (username, domain.name)).encode('utf-8'))
            except User.DoesNotExist:
                print((u"create user %s for domain %s" % (username, domain.name)).encode('utf-8'))
                User.default_manager.create(
                    username=username,
                    domain=domain,
                    first_name=u"รายงานข้ามจังหวัด",
                    last_name="",
                    password=time.time()
                )