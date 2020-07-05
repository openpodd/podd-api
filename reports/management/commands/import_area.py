# -*- encoding: utf-8 -*-

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.models import GroupAdministrationArea
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA
from common.functions import get_data_from_csv
from reports.models import AdministrationArea


class Command(BaseCommand):
    args = 'file_path.csv'
    help = 'Import Administration Area with code from csv: file_path.csv'

    def handle(self, *args, **options):
        
        if not args:
            raise CommandError('Please input csv path')

        file_path = args[0]
        data = get_data_from_csv(file_path)

        parent_area = None
        for row in data:
            if not row[u'ชื่อ'] and not row[u'รหัส']:
                continue

            lat = row['lat'] or 13.8082770000000004
            lng = row['lng'] or 100.5522059999999982
            point = 'POINT (%s %s)' % (lng, lat)
            code = row[u'รหัส']

            try:
                parent_area = AdministrationArea.objects.get(code=code)
            except:
                pass
            else:
                continue

            if len(code) == 2:
                name = u'อำเภอ%s' % row[u'ชื่อ']
                address = name

                area = AdministrationArea.objects.create(
                    name = name,
                    address = address,
                    location = point,
                    code = code,
                )
                parent_area = area
            else:
                name = row[u'ชื่อ']
                address = '%s %s' % (name, parent_area.name)

                area = parent_area.add_child(
                    name = name,
                    address = address,
                    location = point,
                    code = code,
                )

            group, created = Group.objects.get_or_create(
                name = address,
                type = GROUP_WORKING_TYPE_ADMINSTRATION_AREA,
            )

            GroupAdministrationArea.objects.create(
                group = group,
                administration_area = area,
            )
