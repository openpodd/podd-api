# -*- encoding: utf-8 -*-

import json

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from django.contrib.gis import geos
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D

from accounts.models import GroupAdministrationArea
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA
from common.functions import get_data_from_csv
from reports.models import AdministrationArea


class Command(BaseCommand):
    args = 'area.geojson'
    help = 'Import Villages Area from geojson: area.geojson'

    def find_area(self, code):
        return AdministrationArea.objects.get(code=code)

    def handle(self, *args, **options):

        if not args:
            raise CommandError('Please input geojson path')

        file_path = args[0]

        data = None
        with open(file_path, 'rb') as json_file:
            data = json.load(json_file)

        data = data['features']

        i = 0
        for row in data:

            g = GEOSGeometry(json.dumps(row['geometry']))
            area = self.find_area(row['properties']['code'])

            if area:
                area.mpoly = (g)
                area.save()

                i = i + 1
                print '(', i, '/', len(data), ')', area.address

            else:
                print 'not found: ', row['properties']['TB_TN'], area


