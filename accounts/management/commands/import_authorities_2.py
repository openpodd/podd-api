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
        areas = []
        authorities = []

        if not args:
            raise CommandError('Please input csv path')

        file_path = args[0]
        data = get_data_from_csv(file_path)

        domain_id = args[1]
        settings.CURRENT_DOMAIN_ID = domain_id


        authority_map = dict()
        inherits_list = []
        # first pass
        print("========= first pass ==========")
        for row in data:
            if row['domain_id'] == domain_id:
                authority = None
                try:
                    authority = Authority.objects.get(code=row['code'])
                except Authority.DoesNotExist:
                    pass
                    # try:
                    #     authority = Authority.objects.get(name=row['name'])
                    # except Authority.DoesNotExist:
                    #     if row['exists'] == 'True':
                    #         authority = Authority.objects.get(pk=row['podd_id'])

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
                        authorities.append(authority)
                        authority.save()
                    else:
                        print 'skip authority %s' % (authority.code)
                else:
                    name = row['name']
                    code = row['code']
                    group = row['group']
                    print 'create authority %s inherits %s %s' % (code, row['inherits'], row['exists'])

                    authority = Authority.objects.create(
                        name=name,
                        code=code,
                        description=name,
                        group=group,
                    )
                    authority.save()
                    address = row['name']
                    if group == 2:
                        address = '%s %s' % (row['name'], row['district_name'])

                    lat = row['lat']
                    lng = row['lng']
                    point = 'POINT (%s %s)' % (lng, lat)

                    area = AdministrationArea.add_root(
                        name=name,
                        address=address,
                        location=point,
                        code=code,
                        authority=authority
                    )
                    areas.append(area)
                    area.save()

                if row['inherits']:
                    inherits = row['inherits'].replace('[', '').replace(']', '').split(',')
                    inherits_list.append((authority, inherits))
                authority_map[authority.code] = authority
                print authority_map[authority.code]

            else:
                print 'Domain id mismatch for %s' % (row['name'],)

        # second pass
        print("========= second pass ==========")
        for (authority, inherits) in inherits_list:
            found = False
            print 'checking inherit for %s -> inherits = %s' % (authority.code, inherits)
            for parent in inherits:
                print 'parent = %s' % (parent, )
                if parent:
                    code = parent.replace('\'', '').strip()
                    print 'check for code = %s' % (code,)
                    print authority_map[code]
                    parent_authority = authority_map[code]
                    print 'parent authority = %s' % (parent_authority.code)
                    if not authority.inherits.filter(code=code).exists():
                        print 'create inherit for %s with %s' % (authority.code, parent_authority.code)
                        authority.inherits.add(parent_authority)
                        found = True
            if found:
                print 'saving inherits relationship for %s' % (authority.code,)
                authority.save()

        # third pass
        print("======== third pass ==========")
        for a in Authority.objects.filter(domain_id=domain_id):
            print '.'
            a.update_graph_relations()

        for a in AdministrationArea.objects.filter(domain_id=domain_id):
            print 'x'
            a.update_graph_relations()


