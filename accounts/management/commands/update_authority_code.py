# -*- encoding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Authority
from common.functions import get_data_from_csv
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

        # first pass
        print("========= first pass ==========")
        for row in data:
            if row['domain_id'] == domain_id:
                authority = None

                try:
                    authority = Authority.objects.get(name=row['name'])
                except Authority.DoesNotExist:
                    try:
                        authority = Authority.objects.get(code=row['code'])
                    except Authority.DoesNotExist:
                        if row['exists'] == 'True':
                            authority = Authority.objects.get(pk=row['podd_id'])


                # update existing authority code, group
                if authority:
                    if (authority.code != row['code']) or (authority.group != int(row['group'])):
                        print 'update authority %s' % (authority.code)
                        print authority.code != row['code']
                        print authority.group != int(row['group'])
                        print authority.code
                        print row['code']
                        authority.code = row['code']
                        authority.group = int(row['group'])
                        authority.save()
                    else:
                        print 'skip authority %s' % (authority.code)

            else:
                print 'Domain id mismatch for %s' % (row['name'],)



