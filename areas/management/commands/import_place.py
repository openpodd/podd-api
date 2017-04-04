# -*- encoding: utf-8 -*-
import codecs
import csv
from django.conf import settings

from django.core.management.base import BaseCommand, CommandError
from areas.models import PlaceCategory, Place


class Command(BaseCommand):
    args = 'file_path.csv'
    help = 'python manage.py import_place <domain_id> <category_code> <file_pate.csv>'

    def csv_reader(self, utf8_data, **kwargs):
        csv_reader = csv.DictReader(utf8_data, **kwargs)
        for row in csv_reader:
            yield {unicode(key, 'utf-8'): unicode(value, 'utf-8') for key, value in row.iteritems()}

    def handle(self, *args, **options):

        if len(args) < 3:
            raise CommandError('Arguments error')

        domain_id, category_code, file_path = args

        settings.CURRENT_DOMAIN_ID = int(domain_id)

        category, created = PlaceCategory.objects.get_or_create(code=category_code, defaults={
            'code': category_code,
            'name': category_code
        })
        update_category = False

        update_count = 0
        create_count = 0
        csv_data = self.csv_reader(open(file_path, 'r'))
        for data in csv_data:
            data['domain_id'] = domain_id
            data['category'] = category

            if data.get('level1_name') and not category.level1_key:
                category.level1_key = 'level1'
                category.level1_label = 'Level1'
                update_category = True

            if data.get('level2_name') and not category.level2_key:
                category.level2_key = 'level2'
                category.level2_label = 'Level2'
                update_category = True

            #print data
            place = Place(**data)
            if place.save():
                create_count += 1
                print '+',
            else:
                update_count += 1
                print '.',


        if update_category:
            category.save()

        print ''
        print 'Create: %s places, Update: %s places' %(create_count, update_count)




