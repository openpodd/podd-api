# -*- encoding: utf-8 -*-
from django.conf import settings

from django.core.management.base import BaseCommand, CommandError
import uuid
from accounts.models import Authority, User
from common.constants import USER_STATUS_PUBLIC_HEALTH

from common.functions import get_data_from_csv
from terminaltables import AsciiTable

class Command(BaseCommand):
    args = 'file_path.csv'
    help = 'Import Hospital Authority'

    def handle(self, *args, **options):

        settings.CURRENT_DOMAIN_ID = 1
        
        if not args:
            raise CommandError('Please input csv path')

        file_path = args[0]
        data = get_data_from_csv(file_path)

        Authority.objects.filter(name__contains=u'ป่าไหน').update(name=u'เทศบาลตำบลป่าไหน่')
        Authority.objects.filter(name__contains=u'องค์การบริหารส่วนตำบลต้นหมื้อ').update(name=u'องค์การบริหารส่วนตำบลสันต้นหมื้อ')
        Authority.objects.filter(name__contains=u'องค์การบริหารส่วนตำบลกื๊ดช้าง').update(name=u'องค์การบริหารส่วนตำบลกื้ดช้าง')

        table_data = [[u'name', u'level1', u'level2', u'user']]

        map_authority = {
            u'ทุ่งหลวง': u'เทศบาลตำบลเวียงพร้าว',
            u'ปงตำ': u'องค์การบริหารส่วนตำบลปงตำ',
            u'แม่แฝกใหม่': u'องค์การบริหารส่วนตำบลแม่แฝกใหม่',
            u'ริมใต้': u'เทศบาลตำบลแม่ริม',
            u'กืดช้าง': u'องค์การบริหารส่วนตำบลกื้ดช้าง',
            u'ช่อแล': u'เทศบาลเมืองเมืองแกนพัฒนา',
            u'ขี้เหล็ก': u'เทศบาลตำบลจอมแจ้ง',
            u'สำราญราฏร์': u'เทศบาลตำบลสำราญราษฎร์',
            u'ป่าลาน': u'เทศบาลตำบลดอยสะเก็ด',
            u'ศรีภูมิ': u'เจ้าหน้าที่',
            u'หายยา': u'เจ้าหน้าที่',
            u'ช้างม่อย': u'เจ้าหน้าที่',
            u'ช้างคลาน': u'เจ้าหน้าที่',
            u'วัดเกตุ': u'เจ้าหน้าที่',
            u'ป่าตัน': u'เจ้าหน้าที่'
        }

        for row in data:
            #level0 = Authority.objects.filter(name__icontains=row['level0']).first()
            level1_name = (u'อำเภอ' + row["level1"]).replace(u'ฯ', u'')
            level1 = Authority.objects.filter(name__icontains=level1_name).first()

            level2 = Authority.objects.filter(inherits=level1, name__icontains=row['level2']).first()

            name = row["name"].replace(' ', '')
            if not name.startswith(row["note"]):
                name = '%s%s' % (row["note"], name)

            name = name.replace('PCU.', 'PCU')
            name = name.replace('PCU', 'PCU ')

            if not level2:
                try:
                    level2 = Authority.objects.get(name=map_authority[row['level2']])
                except Authority.DoesNotExist:
                    print map_authority[row['level2']]
                    level2 = Authority.objects.create(name=map_authority[row['level2']], code=str(uuid.uuid4())[:8])
                    level2.inherits.add(level1)

            try:
                user = User.objects.get(username=row['code'])
            except User.DoesNotExist:
                user = User.objects.create(username=row['code'], password=row['code'], status=USER_STATUS_PUBLIC_HEALTH, display_password=True)
                user.set_password(row['code'][-4:])
                user.save()

            level2.users.add(user)

            table_data.append([name, (level1 and level1.name) or u'?????', (level2 and level2.name) or (u'????? ' + row['level2']), user])

        table = AsciiTable(table_data)
        print table.table
