# -*- encoding: utf-8 -*-
import difflib
import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from accounts.models import Authority
from reports.models import Report, ReportType, ReportState, AdministrationArea
import codecs

class Command(BaseCommand):
    args = '<domain_id domain_id ...>'
    help = 'Generate SaTScan from report'

    def handle(self, *args, **options):

        report_type = ReportType.objects.get(code='1085ca98-c3ad-11e4-b')

        report_states = ['Case', 'Suspect Outbreak', 'No Outbreak Identified', 'Outbreak', 'Finish']
        report_states = ReportState.objects.filter(report_type=report_type, name__in=report_states)
        area_list = list(AdministrationArea.objects.filter(domain_id=1).values_list('name', flat=True))


        # create the folder if it doesn't exist.
        directory = 'satscan'
        directory_path = os.path.join(settings.MEDIA_ROOT, directory)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)


        # Discrete Poisson Model =========================================================================

        age_dict = {
            u'ระยะแรกเกิด': 1,
            u'ระยะแรกเกิด,ระยะรุ่น': 2,
            u'ระยะรุ่น': 3,
            u'ระยะรุ่น,ระยะพ่อแม่พันธุ์': 4,
            u'ระยะพ่อแม่พันธุ์': 5,
            u'ระยะแรกเกิด,ระยะพ่อแม่พันธุ์': 6,
            u'ระยะแรกเกิด,ระยะรุ่น,ระยะพ่อแม่พันธุ์': 7
        }


        pop_json_file_path = os.path.join(settings.STATIC_ROOT, 'area', 'animal-pop.geojson')
        pop_json_file = codecs.open(pop_json_file_path)
        pop_json_data = json.load(pop_json_file)

        cas_file_path = os.path.join(settings.MEDIA_ROOT, directory, '%s.cas' % 'DiscretePoissonModel')
        cas_file = codecs.open(cas_file_path, 'w', 'utf-8')
        geo_file_path = os.path.join(settings.MEDIA_ROOT, directory, '%s.geo' % 'DiscretePoissonModel')
        geo_file = codecs.open(geo_file_path, 'w', 'utf-8')
        pop_file_path = os.path.join(settings.MEDIA_ROOT, directory, '%s.pop' % 'DiscretePoissonModel')
        pop_file = codecs.open(pop_file_path, 'w', 'utf-8')

        cas_output = ''
        geo_output = ''
        pop_output = ''

        area_dict = {}

        for pop_area in pop_json_data['features']:

            properties = pop_area['properties']

            try:
                authority = Authority.objects.filter(name__contains=properties['TB_TN'], inherits__name__contains=properties['AP_TN']).latest('id')
            except Authority.DoesNotExist:
                similar_area_name = difflib.get_close_matches(properties['TB_TN'], area_list, cutoff=0)[0]
                try:
                    similar_area = AdministrationArea.objects.get(name=similar_area_name)
                    authority = similar_area.authority
                    print 'Found similar: ', properties['TB_TN'], similar_area.name, authority.name
                except AdministrationArea.MultipleObjectsReturned:
                    try:
                        similar_area = AdministrationArea.objects.filter(name=similar_area_name, authority__inherits__name__contains=properties['AP_TN']).latest('id')
                    except AdministrationArea.DoesNotExist:
                        similar_area = AdministrationArea.objects.filter(name=similar_area_name).latest('id')

                    authority = similar_area.authority
                    print 'Found multiple similar: ', properties['TB_TN'], similar_area.name, authority.name


            area_key = '%s--%s' % (authority.id, authority.name.replace(' ', '-'))

            sum_keys = [u'ไก่พื้นเมื', u'นกเอี้ยง', u'เป็ดเทศ', u'ไก่ไข่', u'ไก่ไข่พันธ', u'นก_สัตว์ปี', u'เป็ดไข่', u'เป็ด', u'ไก่งวง', u'ไก่', u'ไก่เนื้อพั', u'พันธุ์ไข่', u'เป็ดเนื้อ', u'เป็ดไข่ไล่']
            sum_pop = 0
            for k, v in properties.items():
                if k in sum_keys:
                    sum_pop += int(v)

            try:
                area_dict[area_key]
            except KeyError:
                area_dict[area_key] = 0

            area_dict[area_key] += sum_pop


        for area_key, sum_pop in area_dict.items():
            # <county> <year> <population> <age group> <sex>
            authority = Authority.objects.get(id=area_key.split('--')[0])
            location = authority.get_location()
            if not location:
                print 'Error not found location: ', authority.name
            else:
                geo_output += '%s %s %s\n' % (area_key, location['y'], location['x'])
                pop_output += '%s 2015 %s %s 1\n' % (area_key, sum_pop, 3, )


        reports = Report.objects.filter(
            type=report_type,
            state__in=report_states,
            test_flag=False,
            form_data__contains='"animalGroup": "\u0e2a\u0e31\u0e15\u0e27\u0e4c\u0e1b\u0e35\u0e01"'
        )

        for report in reports:
            # <county> <cases=1> <year> <age group> <sex>


            data = json.loads(report.form_data)

            authority = report.administration_area.authority

            area_key = '%s--%s' % (authority.id, authority.name.replace(' ', '-'))

            if area_dict.get(area_key):
                cas_output += '%s 1 %s %s 1\n' % (area_key, report.date.strftime('%Y/%m/%d'), 3)

        cas_file.write(cas_output)
        geo_file.write(geo_output)
        pop_file.write(pop_output)


        # Space-Time permutation model  =========================================================================

        cas_file_path = os.path.join(settings.MEDIA_ROOT, directory, '%s.cas' % 'SpaceTimeModel')
        cas_file = codecs.open(cas_file_path, 'w', 'utf-8')
        geo_file_path = os.path.join(settings.MEDIA_ROOT, directory, '%s.geo' % 'SpaceTimeModel')
        geo_file = codecs.open(geo_file_path, 'w', 'utf-8')

        # Case file
        cas_output = ''
        geo_output = ''

        reports = Report.objects.filter(
            type=report_type,
            state__in=report_states,
            test_flag=False,
            parent__isnull=True,
            form_data__contains='"animalGroup": "\u0e2a\u0e31\u0e15\u0e27\u0e4c\u0e1b\u0e35\u0e01"'
        ).order_by('-date')
        area_dict = {}

        for report in reports:
            data = json.loads(report.form_data)

            area = report.administration_area

            if not area.authority:
                continue

            area_key = '%s--%s--%s' % (area.id, area.authority.name.replace(' ', '-'), area.name.replace(' ', '-'))
            if not area_dict.get(area_key):
                area_dict[area_key] = True
                geo_output += '%s %s %s\n' % (area_key, area.location.y, area.location.x)

            numCase = int(data['deathCount']) + int(data['sickCount']) + int(data['nearByCount'])
            numCase = 1
            cas_output += numCase*('%s 1 %s\n' % (area_key, report.date.strftime('%Y/%-m/%-d')))

        cas_file.write(cas_output)
        geo_file.write(geo_output)