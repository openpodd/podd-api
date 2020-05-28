# -*- encoding: utf-8 -*-
import xlrd

from accounts.models import Authority
from notifications.models import NotificationTemplate, NotificationAuthority


def import_notification_excel(template_id, file):
    template = NotificationTemplate.objects.get(id=template_id)

    try:
        xl_book = xlrd.open_workbook(file_contents=file.read())
        for sheet_idx in range(0, xl_book.nsheets):
            xl_sheet = xl_book.sheet_by_index(sheet_idx)
            
            for row_idx in range(1, xl_sheet.nrows):
                authority_code = xl_sheet.cell(row_idx, 1).value
                to = xl_sheet.cell(row_idx, 3).value

                if authority_code:
                    authority = Authority.objects.get(code=authority_code)
                    # print '%s %s %s' % (template.id, authority.id, to)
                    # print 'INSERT INTO "notifications_notificationauthority" ("is_deleted", "template_id", "authority_id", "to") SELECT false, %s, %s, \'%s\' WHERE NOT EXISTS ( SELECT id, "is_deleted", "template_id", "authority_id", "to" FROM notifications_notificationauthority WHERE template_id = %s AND authority_id = %s AND "to" = \'%s\');' % (template.id, authority.id, to, template.id, authority.id, to)
                    notificationAuthority, create = NotificationAuthority.objects.get_or_create(template=template, authority=authority)
                    notificationAuthority.to = to
                    notificationAuthority.save()
        return True
    except:
        return False 
