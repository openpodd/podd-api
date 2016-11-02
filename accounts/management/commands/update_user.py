# -*- encoding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from common.constants import USER_STATUS_VOLUNTEER
from common.functions import get_data_from_csv


class Command(BaseCommand):
    args = 'file_path.csv'
    help = 'Import Users from csv: file_path.csv'

    def handle(self, *args, **options):

        if not args:
            raise CommandError('Please input csv path')

        file_path = args[0]
        data = get_data_from_csv(file_path)

        for row in data:
            username = row['PODD Username']

            if not username:
                continue

            # address and tel.
            contact = row[u'ที่อยู่']
            telephone = row[u'เบอร์โทร']
            project_mobile_number = row[u'Mobile Number']
            serial_number = row[u'S/N']
            running_number = row[u'เลขที่ running']
            note = row[u'หมายเหตุ']
            display_password = row[u'PODD Password']

            try:
                # try update if found existing user.
                user = User.objects.get(username=username)

                # do an update
                user.contact = contact
                user.telephone = telephone
                user.project_mobile_number = project_mobile_number
                user.serial_number = serial_number
                user.running_number = running_number
                user.note = note
                user.display_password = display_password
                user.status = USER_STATUS_VOLUNTEER

                user.save()

                print 'Updated %s' % (username, )
            except User.DoesNotExist:
                # if not then continue
                continue
