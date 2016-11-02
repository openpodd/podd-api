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
    help = 'Import Tambon Area from geojson: area.geojson'


    def find_area(self, g, name, parent_name):
        if parent_name == u'เมืองเชียงใหม่':
            parent_name = u'เมือง'

        areas = [ area for area in AdministrationArea.objects.exclude(code__startswith='public_1').filter(parent__name__contains=parent_name,
                                                                                                          name__contains=name) if not area.get_children()]
        if len(areas):
            return areas[0]
        else:
            areas = [ area for area in AdministrationArea.objects.exclude(code__startswith='public_1').filter(parent__name__contains=parent_name)]
            areas.sort(key=lambda x: g.distance(x.location))
            return areas[0] if len(areas) else None

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
            area = self.find_area(g, row['properties']['TB_TN'], row['properties']['AP_TN'])

            if area:

                area.mpoly = geos.MultiPolygon(g)
                area.qgis_id = '%s, %s' % (area.qgis_id, row['properties']['TB_IDN']) if area.qgis_id else row['properties']['TB_IDN']
                area.save()

                i = i + 1

                print '(', i, '/', len(data), ')', row['properties']['AP_TN'], row['properties']['TB_TN'], area.name
            else:
                print 'not found: ', row['properties']['TB_TN']


