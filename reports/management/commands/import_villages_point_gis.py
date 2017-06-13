# -*- encoding: utf-8 -*-

import json

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from django.contrib.gis import geos
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.conf import settings

from accounts.models import GroupAdministrationArea
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA
from common.functions import get_data_from_csv
from reports.models import AdministrationArea


class Command(BaseCommand):
    args = 'area.geojson domain_id'
    help = 'Import Villages Area from geojson: area.geojson'

    def find_parent_area(self, tb_idn):
        areas = [ area for area in AdministrationArea.objects.filter(qgis_id__contains=tb_idn).order_by('id')]
        if len(areas):
            return areas[0]
        else:
            return None

    def handle(self, *args, **options):

        if not args:
            raise CommandError('Please input geojson path')

        domain_id = args[1]
        settings.CURRENT_DOMAIN_ID = domain_id

        file_path = args[0]

        data = None
        with open(file_path, 'rb') as json_file:
            data = json.load(json_file)

        data = data['features']
        i = 0

        for row in data:

            point = GEOSGeometry(json.dumps(row['geometry']))
            parent_area = self.find_parent_area(row['properties']['TA_ID'])

            if parent_area:
                code = '%s-%s' % (parent_area.code, (int)(row['properties']['FID_L08_Vi']))
                try:
                    area = AdministrationArea.objects.get(qgis_id=row['properties']['FID_L08_Vi'])
                    area.name = u'บ้าน%s' % row['properties']['V_Name_T']
                    area.address = u'บ้าน%s %s' % (row['properties']['V_Name_T'], parent_area.address)
                    area.location = point
                    area.code = code
                    if not area.authority:
                        area.authority = parent_area.authority
                    area.save()
                except AdministrationArea.DoesNotExist:
                    area = AdministrationArea.objects.create(
                        name=u'บ้าน%s' % row['properties']['V_Name_T'],
                        address=u'บ้าน%s %s' % (row['properties']['V_Name_T'], parent_area.address),
                        location=(point),
                        code=code,
                        qgis_id=row['properties']['FID_L08_Vi'],
                        authority=parent_area.authority
                    )

                i = i + 1
                print '(', i, '/', len(data), ')', area.address, area.authority.name
            else:
                pass
                # print 'not found: ', (row['properties']['V_Name_T'])


