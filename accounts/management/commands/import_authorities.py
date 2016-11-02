# -*- encoding: utf-8 -*-

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.models import GroupAdministrationArea
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA
from common.functions import get_data_from_csv
from accounts.models import Authority, User
from reports.models import AdministrationArea


class Command(BaseCommand):
    args = 'file_path.csv'
    help = 'Import Administration Area with code from csv: file_path.csv'

    def handle(self, *args, **options):
        
        if not args:
            raise CommandError('Please input csv path')

        file_path = args[0]
        data = get_data_from_csv(file_path)

        for row in data:

            name = row['name']
            address = row['address'] or name
            code = row['code']
            lat = row['lat'] or 13.8082770000000004
            lng = row['lng'] or 100.5522059999999982
            point = 'POINT (%s %s)' % (lng, lat)
            parent = row['parent_pk']

            try:
                parent = Authority.objects.get(id=parent)
            except Authority.DoesNotExist:
                continue

            authority = Authority.objects.create(
                name=name,
                code=code,
                description=address or name,
                domain=parent.domain,
            )

            authority.inherits.add(parent)
            area = AdministrationArea.add_root(
                name=name,
                address=address or name,
                location=point,
                code=code,
                authority=authority,
                domain=parent.domain,
            )
            print 'area: ', area
