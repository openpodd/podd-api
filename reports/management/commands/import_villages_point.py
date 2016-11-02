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
    args = 'area.geojson'
    help = 'Import Villages Area from geojson: area.geojson'

    def find_parent_area(self, tb_idn):
        areas = [ area for area in AdministrationArea.objects.filter(qgis_id__contains=tb_idn).order_by('id')]
        if len(areas):
            return areas[0]
        else:
            return None

    def handle(self, *args, **options):
        settings.CURRENT_DOMAIN_ID = 1

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
            point = point[0]

            parent_area = self.find_parent_area(row['properties']['tb_idn'])

            if parent_area:
                code = '%s-%04d' % (parent_area.code, (int)(row['properties']['village_id']))
                try:
                    area = AdministrationArea.objects.get(qgis_id=row['properties']['vill_code'])
                    area.name = u'บ้าน%s' % row['properties']['vill_nam_t']
                    area.address = u'บ้าน%s %s' % (row['properties']['vill_nam_t'], parent_area.address)
                    area.location = point
                    area.code = code
                    if not area.authority:
                        area.authority = parent_area.authority
                    area.save()
                except AdministrationArea.DoesNotExist:
                    area = AdministrationArea.objects.create(
                        name=u'บ้าน%s' % row['properties']['vill_nam_t'],
                        address=u'บ้าน%s %s' % (row['properties']['vill_nam_t'], parent_area.address),
                        location=(point),
                        code=code,
                        qgis_id=row['properties']['vill_code'],
                        domain=parent_area.domain
                    )

                i = i + 1
                print '(', i, '/', len(data), ')', area.address
            else:
                print 'not found: ', (row['properties']['vill_nam_t'])


