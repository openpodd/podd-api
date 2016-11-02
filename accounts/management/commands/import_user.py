# -*- encoding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from accounts.models import GroupAdministrationArea, User
from common.factory import randnum
from common.functions import get_data_from_csv


class Command(BaseCommand):
    args = 'file_path.csv'
    help = 'Import Users from csv: file_path.csv'

    def handle(self, *args, **options):

        if not args:
            raise CommandError('Please input csv path')

        file_path = args[0]
        data = get_data_from_csv(file_path)

        amphoe = None
        subdivision = None
        group = None
        for row in data:
            if row[u'อำเภอ']:
                amphoe = row[u'อำเภอ']

            if row[u'อปท.']:
                subdivision = row[u'อปท.']
                try:
                    group = GroupAdministrationArea.objects.get(administration_area__name=subdivision)
                except:
                    group = None
                    print 'Subdivision %s not found.' % subdivision

            if not row[u'รายชื่ออาสาสมัคร']:
                continue

            if group:
                code = group.administration_area.code

                (number, fullname) = row[u'รายชื่ออาสาสมัคร'].split('.', 1)
                (firstname, lastname) = fullname.split(' ', 1)

                # address and tel.
                contact = row[u'ที่อยู่']
                telephone = row[u'เบอร์โทร']
                project_mobile_number = row[u'Mobile Number']

                if not row['PODD Username']:
                    username = 'podd.%s.%02d' % (code, int(number))
                    password = '%06d' % randnum()

                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=firstname,
                        last_name=lastname,
                        administration_area=group.administration_area,
                        contact=contact,
                        telephone=telephone,
                        project_mobile_number=project_mobile_number,
                    )

                    user.groups.add(group.group)

                    print 'Created %s,%s,%s,%s' % (firstname, lastname, username, password)
                else:
                    username = row['PODD Username']

                    try:
                        # try update if found existing user.
                        user = User.objects.get(username=username)

                        # do an update
                        user.contact = contact
                        user.telephone = telephone
                        user.project_mobile_number = project_mobile_number

                        user.save()

                        print 'Updated %s' % (username, )
                    except User.DoesNotExist:
                        # if not then create instead
                        password = row['PODD Passwod']

                        user = User.objects.create_user(
                            username=username,
                            password=password,
                            first_name=firstname,
                            last_name=lastname,
                            administration_area=group.administration_area,
                            contact=contact,
                            telephone=telephone,
                            project_mobile_number=project_mobile_number,
                        )

                        user.groups.add(group.group)

                        print 'Created %s,%s,%s,%s' % (firstname, lastname, username, password)
