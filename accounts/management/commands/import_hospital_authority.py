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

        table_data = [[u'name', u'level1', u'level2', u'user', u'latitude', u'longitude']]

        map_authority = {
        }

        for row in data:
            #level0 = Authority.objects.filter(name__icontains=row['level0']).first()
            level1_name = (u'อำเภอ' + row["level1"]).replace(u'ฯ', u'')
            level1 = Authority.objects.filter(name__icontains=level1_name).first()

            level2 = Authority.objects.filter(inherits=level1, name__icontains=row['level2']).first()

            name = row["name"].replace(' ', '')
            if not name.startswith(row["note"]):
                name = '%s%s' % (row["note"], name)

            if not level2:
                try:
                    level2 = Authority.objects.get(name=row['level2'])
                except Authority.DoesNotExist:
                    pass
                    #print row['level2']
                    level2 = Authority.objects.create(name=row['level2'], code=str(uuid.uuid4())[:8])
                    level2.inherits.add(level1)

                    AdministrationArea.add_root(
                        name=row['level2'],
                        address=row['level2'],
                        location='POINT (%s %s)' % (row['longitude'], row['latitude']),
                        code='area-%s-%s' % (settings.CURRENT_DOMAIN_ID, row['code']),
                        authority=level2,
                    )


            try:
                user = User.objects.get(username=row['code'])
            except User.DoesNotExist:
                user = User.objects.create(username=row['code'], password=row['code'], status=USER_STATUS_PUBLIC_HEALTH, display_password=True)
                user.set_password(row['code'])
                user.save()
                level2.users.add(user)

            table_data.append([name, (level1 and level1.name) or u'?????', (level2 and level2.name) or (u'????? ' + row['level2']), user, row['latitude'], row['longitude']])

        table = AsciiTable(table_data)
        print table.table
