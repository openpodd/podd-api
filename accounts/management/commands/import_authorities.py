# -*- encoding: utf-8 -*-
from django.conf import settings

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.models import GroupAdministrationArea
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA
from common.functions import get_data_from_csv
from accounts.models import Authority, User
from reports.models import AdministrationArea


class Command(BaseCommand):
    args = 'file_path.csv domain_id'
    help = 'Import Authority with code from csv: file_path.csv'

    def handle(self, *args, **options):
        
        if not args:
            raise CommandError('Please input csv path')

        file_path = args[0]
        data = get_data_from_csv(file_path)

        domain_id = args[1]
        settings.CURRENT_DOMAIN_ID = domain_id


        for row in data:

            name = row['name']
            address = row['address'] or name
            code = row['code']
            code_address = row['code_address']
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
                description=address or name
            )

            authority.inherits.add(parent)
            area = AdministrationArea.add_root(
                name=name,
                address=address or name,
                location=point,
                code=code_address,
                authority=authority,
                qgis_id=code_address
            )

            # save for update elasticsearch, graph-neo4j
            authority.save()

            print 'Authority: ', area
