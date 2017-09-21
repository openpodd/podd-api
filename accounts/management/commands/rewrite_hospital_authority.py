# -*- encoding: utf-8 -*-
from django.conf import settings
from django.contrib.gis.geos import Point

from django.core.management.base import BaseCommand, CommandError
import uuid
from accounts.models import Authority, User
from common.constants import USER_STATUS_PUBLIC_HEALTH

from common.functions import get_data_from_csv
from terminaltables import AsciiTable
from reports.models import AdministrationArea


class Command(BaseCommand):
    args = 'file_path.csv'
    help = 'Import Hospital Authority'

    def handle(self, *args, **options):

        settings.CURRENT_DOMAIN_ID = 7
        
        if not args:
            raise CommandError('Please input csv path')

        file_path = args[0]
        data = get_data_from_csv(file_path)

        table_data = [[u'name', u'level1', u'level2', u'level2x', u'user', u'latitude', u'longitude']]

        map_authority = {
        }

        for row in data:

            try:
                area = AdministrationArea.objects.get(code='area-%s-%s' % (settings.CURRENT_DOMAIN_ID, row['code']))
            except AdministrationArea.DoesNotExist:
                continue

            authority = area.authority

            AdministrationArea.objects.filter(id=area.id).update(name=row['level2'], address=row['level2'])

            if Authority.objects.filter(name=row['level2']).exclude(id=authority.id).count() > 0:
                authority.delete()
            else:
                Authority.objects.filter(id=authority.id).update(name=row['level2'])

            user = User.objects.get(username=row['code'])
            user.username = row['code'].zfill(5)
            user.set_password(row['code'].zfill(5))
            user.save()


            table_data.append([row['name'], row['level1'], row['level2'], user, row['latitude'], row['longitude']])

        table = AsciiTable(table_data)
        print table.table
