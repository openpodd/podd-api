# -*- encoding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from accounts.models import GroupAdministrationArea, Authority, User, UserDevice
from common.models import Domain


class Command(BaseCommand):
    help = 'Move Users from Elephant to TECC'

    def handle(self, *args, **options):

        try:
            elephant = Domain.objects.get(code='Elephant')
        except Domain.DoesNotExist:
            raise CommandError('No Domain Elephant')

        users = User.objects.filter(domain=elephant)

        try:
            tecc = Domain.objects.get(code='TECC')
        except Domain.DoesNotExist:
            raise CommandError('No Domain TECC')

        i = 0
        for user in users:
            user.domain = tecc
            user.save()
            try:
                user.device.domain = tecc
                user.device.save()
            except UserDevice.DoesNotExist:
                pass

            i += 1
            print '(', i, '/', users.count(), ')', user.get_full_name()

