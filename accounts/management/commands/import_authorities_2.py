# -*- encoding: utf-8 -*-
from django.conf import settings

from django.core.management.base import BaseCommand, CommandError

from common.constants import USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER, USER_STATUS_PUBLIC_HEALTH
from common.functions import get_data_from_csv
from accounts.models import Authority, User, AuthorityInvite
from reports.models import AdministrationArea
from django.db import transaction


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

        sid = transaction.savepoint()
        print("========= first pass ==========")
        try:
            # first pass
            # update existing authority code, group
            for row in data:
                if row['domain_id'] == domain_id:
                    if row['exists'] == 'True':
                        code = row['code']
                        group = row['group']
                        podd_id = row['podd_id']
                        print code

                        try:
                            authority = Authority.objects.get(pk=podd_id)
                        except Authority.DoesNotExist:
                            try:
                                authority = Authority.objects.get(name=row['name'])
                            except Authority.DoesNotExist:
                                authority = None
                        if authority:
                            authority.code = code
                            authority.group = group
                            authority.save()
                        else:
                            print 'Authority %s not found' % (row['name'],)
                else:
                    print 'Domain id mismatch for %s' % (row['name'],)

            # second pass
            # create authority and administrationArea
            print("========= second pass ==========")
            for row in data:
                if row['domain_id'] == domain_id:
                    if row['exists'] == 'False':

                        name = row['name']
                        code = row['code']
                        group = row['group']
                        print 'create authority %s inherits %s %s' % (code, row['inherits'], row['exists'])

                        inherits = row['inherits'].replace('[', '').replace(']', '').split(',')
                        inheritsAuth = []
                        for parent in inherits:
                            if parent:
                                p = Authority.objects.get(code=parent.replace('\'', ''))
                                inheritsAuth.append(p)

                        authority = Authority.objects.create(
                            name=name,
                            code=code,
                            description=name,
                            group=group,
                        )
                        if len(inheritsAuth) > 0:
                            authority.inherits.add(*inheritsAuth)

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

                        ph_invite = AuthorityInvite(
                            authority=authority,
                            status=USER_STATUS_PUBLIC_HEALTH
                        )

                        # save for update elasticsearch, graph-neo4j
                        authority.save()
                        ph_invite.save()

                        print 'Authority: ', area
            transaction.commit(sid)
        except Exception as e:
            print e
            transaction.rollback(sid)

