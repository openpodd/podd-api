# -*- encoding: utf-8 -*-

import json

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from django.contrib.gis import geos
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.conf import settings

from accounts.models import GroupAdministrationArea, Authority
from common.models import Domain
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA
from common.functions import get_data_from_csv
from reports.models import AdministrationArea
from django.db import IntegrityError


class Command(BaseCommand):
    args = 'area.geojson'
    help = 'Import TECC Area from geojson: area.geojson'

    def handle(self, *args, **options):
        try:
            domain = Domain.objects.get(code='TECC')
            settings.CURRENT_DOMAIN_ID = domain.id
        except Domain.DoesNotExist:
            raise CommandError('No Domain TECC')

        if not args:
            raise CommandError('Please input geojson path')

        file_path = args[0]

        data = None
        with open(file_path, 'rb') as json_file:
            data = json.load(json_file)

        data = data['features']
        i = 0

        for row in data:
            point = GEOSGeometry(json.dumps(row['geometry']))
            code = row['properties']['code']
            try:
                authority = Authority.objects.get(name=row['properties']['name'])
            except Authority.DoesNotExist:
                try:
                    authority = Authority.objects.create(
                        name=row['properties']['name'],
                        code=code,
                        domain=domain
                    )
                except IntegrityError:
                    i = i + 1
                    print '(', i, '/', len(data), ')', 'error:', area.address
                    continue
            try:
                area = AdministrationArea.objects.get(code=row['properties']['code'])
                area.name = row['properties']['name']
                area.address = row['properties']['address']
                area.location = point
                area.code = code
                if not area.authority:
                    area.authority = authority
                area.save()
            except AdministrationArea.DoesNotExist:
                area = AdministrationArea.objects.create(
                    name=row['properties']['name'],
                    address=row['properties']['address'],
                    location=(point),
                    code=code,
                    authority=authority,
                    domain=domain
                )
            i = i + 1
            print '(', i, '/', len(data), ')', area.address

