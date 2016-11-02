# -*- encoding: utf-8 -*-
import xlrd
import xlwt

from django.contrib.gis.geos import Point
from django.http import HttpResponse

from accounts.models import User, Authority, GroupAdministrationArea
from common.constants import (USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER,
    USER_STATUS_COORDINATOR, USER_STATUS_PODD, USER_STATUS_LIVESTOCK, USER_STATUS_PUBLIC_HEALTH,
    GROUP_WORKING_TYPE_ADMINSTRATION_AREA, GROUP_WORKING_TYPE_REPORT_TYPE)
from common.factory import randnum, randstr
from common.functions import generate_username
from reports.models import ReportType, AdministrationArea


def get_querystring_filter_user_status(querystring, status):
    querystring = querystring or {}
    status_lower = status.lower()
    if status_lower == 'volunteer':
        querystring.update({
            'status__in': [
                USER_STATUS_VOLUNTEER,
                USER_STATUS_COORDINATOR],
            'is_anonymous': False,
            'is_public': False
        })
    elif status_lower == 'additional-volunteer':
        querystring.update({
            'status': USER_STATUS_ADDITION_VOLUNTEER,
            'is_anonymous': False,
            'is_public': False
        })
    elif status_lower == 'additional-volunteer-dodd':
        querystring.update({
            'status': USER_STATUS_ADDITION_VOLUNTEER,
            'is_anonymous': False,
            'is_public': True
        })
    elif status_lower == 'podd':
        querystring.update({
            'status': USER_STATUS_PODD
        })
    elif status_lower == 'livestock':
        querystring.update({
            'status': USER_STATUS_LIVESTOCK
        })
    elif status_lower == 'public-health':
        querystring.update({
            'status': USER_STATUS_PUBLIC_HEALTH
        })

    return querystring


class _User:
    def __init__(self, username, first_name, last_name, administration_area, serial_number, telephone, email):
        self.username = username or randstr()
        self.first_name = first_name
        self.last_name = last_name
        self.administration_area = administration_area
        self.serial_number = serial_number
        self.telephone = telephone
        self.email = email


class _Authority:
    def __init__(self, id, code, name, description, administration_area):
        self.id = id
        self.code = code
        self.name = name
        self.description = description if description else name
        self.administration_area = administration_area
        self.users = []

    def add_user(self, user):
        self.users.append(user)


def export_excel_users_to_create_authorities():

    print "Start..."
    authorities = {}
    header = [
                [0, 0, 0, 0, u'authority_name'],
                [0, 0, 1, 1, u'authority_code'],
                [0, 0, 2, 2, u'authority_areas'],
                [0, 0, 3, 3, u'authority_users'],
            ]

    for user in User.objects.filter(username__startswith='podd.').order_by('id'):
        group_administration_areas = user.groups.filter(type=GROUP_WORKING_TYPE_ADMINSTRATION_AREA).order_by('id')
        administration_areas = AdministrationArea.objects.filter(groupadministrationarea__group__in=group_administration_areas)
        
        if not administration_areas.count() == 1:
            continue

        administration_area = administration_areas[0]
        if not administration_area.is_leaf():
            continue

        id = administration_area.id
        name = administration_area.name
        code = administration_area.code
        description = ''

        if not code:
            continue

        try:
            authority = authorities[code]
            authority.add_user(user)
        except KeyError:
            authorities[code] = _Authority(id=id, name=name, code=code, 
                description=description, administration_area=administration_area)
            authorities[code].add_user(user)
    
    print "Export..."
    wb = xlwt.Workbook()
    
    fnt = xlwt.Font()
    fnt.bold = True

    al = xlwt.Alignment()
    al.horz = xlwt.Alignment.HORZ_CENTER

    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1

    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['gray25']

    header_style = xlwt.XFStyle()
    header_style.font = fnt
    header_style.borders = borders
    header_style.pattern = pattern
    header_style.alignment = al

    border_style = xlwt.XFStyle()
    border_style.borders = borders

    bold_style = xlwt.XFStyle()
    bold_style.font = fnt

    for key, authority in authorities.iteritems():
        sheetname = '%s. %s%s' % ( authority.id, authority.name[:22], 
            '...' if len(authority.name) > 22 else '' )
        
        ws = wb.add_sheet(sheetname)
        ws.write(0, 0, u'แบบฟอร์มลงทะเบียนในโครงการผ่อดีดี', bold_style)
        ws.write(2, 0, u'ชื่อ', header_style)
        ws.write(3, 0, u'รหัส (สำหรับเจ้าหน้าที่ podd)', header_style)
        ws.write(4, 0, u'รายละเอียด', header_style)
        ws.write_merge(2, 2, 1, 5, authority.name, border_style)
        ws.write_merge(3, 3, 1, 5, authority.code, border_style)
        ws.write_merge(4, 4, 1, 5, authority.description, border_style)

        ws.write(6, 0, u'ต้องการรายงานจาก', bold_style)
        ws.write(7, 0, u'รหัส (สำหรับเจ้าหน้าที่ podd)', header_style)
        ws.write_merge(7, 7, 1, 5, u'ชื่อสังกัด', header_style)
        ws.write(8, 0, u'', border_style)
        ws.write_merge(8, 8, 1, 5, u'', border_style)

        ws.write(10, 0, u'พื้นที่', bold_style)
        ws.write(11, 0, u'รหัส (สำหรับเจ้าหน้าที่ podd)', header_style)
        ws.write_merge(11, 11, 1, 3, u'ชื่อสังกัด', header_style)
        ws.write(11, 4, u'เส้นรุ้ง (latitude)', header_style)
        ws.write(11, 5, u'เส้นแวง (longitude)', header_style)
        ws.write(12, 0, authority.administration_area.code, border_style)
        ws.write_merge(12, 12, 1, 3, authority.administration_area.__unicode__(), border_style)
        ws.write(12, 4, authority.administration_area.location.y, border_style)
        ws.write(12, 5, authority.administration_area.location.x, border_style)

        ws.write(14, 0, u'ผู้ใช้งาน', bold_style)
        ws.write(15, 0, u'บัญชีผู้ใช้งาน (กรณีมีอยู่แล้ว)', header_style)
        ws.write(15, 1, u'ชื่อ', header_style)
        ws.write(15, 2, u'นามสกุล', header_style)
        ws.write(15, 3, u'เลขที่บัตรประจำตัวประชาชน', header_style)
        ws.write(15, 4, u'เบอร์โทรศัพท์', header_style)
        ws.write(15, 5, u'อีเมล', header_style)

        USER_ROW = 16
        for user in authority.users:
            ws.write(USER_ROW, 0, user.username, border_style)
            ws.write(USER_ROW, 1, user.first_name, border_style)
            ws.write(USER_ROW, 2, user.last_name, border_style)
            ws.write(USER_ROW, 3, user.serial_number, border_style)
            ws.write(USER_ROW, 4, user.telephone, border_style)
            ws.write(USER_ROW, 5, user.email, border_style)
            USER_ROW = USER_ROW + 1

    response = HttpResponse(content_type="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=Authorities.xls'
    
    wb.save(response)
    return response


def import_authorities_excel(file):

    try:
        xl_book = xlrd.open_workbook(file_contents=file.read())
        print "Authorities = ", xl_book.nsheets
        for sheet_idx in range(0, xl_book.nsheets):
            xl_sheet = xl_book.sheet_by_index(sheet_idx)
            
            name = xl_sheet.cell(2, 1).value
            code = xl_sheet.cell(3, 1).value or randnum(0, 10000)
            description = xl_sheet.cell(4, 1).value

            try:
                authority = Authority.objects.get(code=code)
                # print authority
            except Authority.DoesNotExist:
                authority = Authority.objects.create(
                    code = code,
                    name = name,
                    description = description
                )

            bool_report_types = False
            bool_administration_areas = False
            bool_users = False
            
            # print "authority: ", authority.name

            idx = 0
            for row_idx in range(6, xl_sheet.nrows):

                if row_idx == idx:
                    continue

                if xl_sheet.cell(row_idx, 0).value == u'ต้องการรายงานจาก':
                    idx = row_idx + 1 
                    bool_report_types = True
                    continue
                elif xl_sheet.cell(row_idx, 0).value == u'พื้นที่':
                    idx = row_idx + 1 
                    bool_administration_areas = True 
                    continue
                elif xl_sheet.cell(row_idx, 0).value == u'ผู้ใช้งาน':
                    idx = row_idx + 1 
                    bool_users = True
                    continue
                elif xl_sheet.cell(row_idx, 0).value == u'' \
                    and xl_sheet.cell(row_idx, 1).value == u'' \
                    and xl_sheet.cell(row_idx, 2).value == u'' \
                    and xl_sheet.cell(row_idx, 3).value == u'' \
                    and xl_sheet.cell(row_idx, 4).value == u'' \
                    and xl_sheet.cell(row_idx, 5).value == u'':
                    bool_report_types = False
                    bool_administration_areas = False
                    bool_users = False

                # Not Yet inherit?
                if bool_report_types:
                    pass

                elif bool_administration_areas:
                    code = xl_sheet.cell(row_idx, 0).value
                    name = xl_sheet.cell(row_idx, 1).value
                    lat = xl_sheet.cell(row_idx, 4).value
                    lon = xl_sheet.cell(row_idx, 5).value
                    parent_id = xl_sheet.cell(row_idx, 6).value
                    address = xl_sheet.cell(row_idx, 7).value
                    
                    if type(lat) == float:
                        lat = float(lat)

                    if type(lon) == float:
                        lon = float(lon)

                    area = None
                    create = True

                    if not code and not name:
                        code = randnum(0, 10000)
                        area = AdministrationArea(code=code, name=name, 
                            location=Point(lon, lat), authority=authority, address=address)
                    elif code:
                        try:
                            area = AdministrationArea.objects.get(code=code)
                            create = False
                        except AdministrationArea.DoesNotExist:
                            area = AdministrationArea(code=code, name=name, 
                                location=Point(lon, lat), authority=authority, address=address)
                            
                    if create and area and parent_id:
                        try:
                            parent_area = AdministrationArea.objects.get(id=parent_id)

                            cl_data =  area.__dict__
                            del cl_data['var_cache']
                            del cl_data['_state']
                            del cl_data['_authority_cache']
                            parent_area.add_child(**cl_data)

                            try:
                                parent_authority = Authority.objects.get(code=parent_area.code)
                                authority.inherits.add(parent_authority)
                            except Authority.DoesNotExist:
                                pass

                        except AdministrationArea.DoesNotExist:
                            pass

                elif bool_users:
                    username = xl_sheet.cell(row_idx, 0).value
                    first_name = xl_sheet.cell(row_idx, 1).value
                    last_name = xl_sheet.cell(row_idx, 2).value
                    serial_number = xl_sheet.cell(row_idx, 3).value
                    telephone = xl_sheet.cell(row_idx, 4).value
                    email = xl_sheet.cell(row_idx, 5).value
                    user = None
                    
                    if not username and first_name:
                        username = randstr()
                        user = User.objects.create(username=username,
                                                    first_name=first_name,
                                                    last_name=last_name,
                                                    serial_number=serial_number,
                                                    telephone=telephone,
                                                    email=email)
                        user.username = generate_username(user.id)
                        user.save()
                    elif username:
                        user, create = User.objects.get_or_create(username=username)
                        user.first_name = first_name
                        user.last_name = last_name
                        user.serial_number = serial_number
                        user.telephone = telephone
                        user.email = email
                    
                    if user:
                        authority.users.add(user)
        return True
    except:
        return False


class __Authority:
    def __init__(self, id, name, lat, lng, parentId, code, address):
        self.id = id
        self.name = name
        self.lat = lat
        self.lng = lng
        self.parentId = parentId
        self.code = code
        self.address = address


def import_and_excel_users_to_create_authorities(file):
    print "Import..."

    authorities = {}

    try:
        xl_book = xlrd.open_workbook(file_contents=file.read())
        xl_sheet = xl_book.sheet_by_index(0)

        idx = 0
        for row_idx in range(1, xl_sheet.nrows):
            id = row_idx
            
            name = xl_sheet.cell(row_idx, 0).value
            lat = xl_sheet.cell(row_idx, 1).value
            lng = xl_sheet.cell(row_idx, 2).value
            parentId = xl_sheet.cell(row_idx, 3).value
            code = xl_sheet.cell(row_idx, 4).value
            address = xl_sheet.cell(row_idx, 5).value

            authority = __Authority(id, name, lat, lng, parentId, code, address)
            authorities[idx] = authority
            idx = idx + 1

    except:
        return False 

    print "Start..."

    header = [
                [0, 0, 0, 0, u'authority_name'],
                [0, 0, 1, 1, u'authority_code'],
                [0, 0, 2, 2, u'authority_areas'],
                [0, 0, 3, 3, u'authority_users'],
            ]
    
    print "Export..."
    wb = xlwt.Workbook()
    
    fnt = xlwt.Font()
    fnt.bold = True

    al = xlwt.Alignment()
    al.horz = xlwt.Alignment.HORZ_CENTER

    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1

    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['gray25']

    header_style = xlwt.XFStyle()
    header_style.font = fnt
    header_style.borders = borders
    header_style.pattern = pattern
    header_style.alignment = al

    border_style = xlwt.XFStyle()
    border_style.borders = borders

    bold_style = xlwt.XFStyle()
    bold_style.font = fnt
    
    count = 0 
    for key, authority in authorities.iteritems():
        sheetname = '%s. %s%s' % ( authority.id, authority.name[:22], 
            '...' if len(authority.name) > 22 else '' )
        
        ws = wb.add_sheet(sheetname)
        ws.write(0, 0, u'แบบฟอร์มลงทะเบียนในโครงการผ่อดีดี', bold_style)
        ws.write(2, 0, u'ชื่อ', header_style)
        ws.write(3, 0, u'รหัส (สำหรับเจ้าหน้าที่ podd)', header_style)
        ws.write(4, 0, u'รายละเอียด', header_style)
        ws.write_merge(2, 2, 1, 5, authority.name, border_style)
        ws.write_merge(3, 3, 1, 5, authority.code, border_style)
        ws.write_merge(4, 4, 1, 5, authority.address, border_style)

        ws.write(6, 0, u'ต้องการรายงานจาก', bold_style)
        ws.write(7, 0, u'รหัส (สำหรับเจ้าหน้าที่ podd)', header_style)
        ws.write_merge(7, 7, 1, 5, u'ชื่อสังกัด', header_style)
        ws.write(8, 0, u'', border_style)
        ws.write_merge(8, 8, 1, 5, u'', border_style)

        ws.write(10, 0, u'พื้นที่', bold_style)
        ws.write(11, 0, u'รหัส (สำหรับเจ้าหน้าที่ podd)', header_style)
        ws.write_merge(11, 11, 1, 3, u'ชื่อสังกัด', header_style)
        ws.write(11, 4, u'เส้นรุ้ง (latitude)', header_style)
        ws.write(11, 5, u'เส้นแวง (longitude)', header_style)
        ws.write(11, 6, u'อำเภอ', header_style)
        ws.write(11, 7, u'ที่อยู่', header_style)
        ws.write(12, 0, authority.code, border_style)
        ws.write_merge(12, 12, 1, 3, authority.name, border_style)
        ws.write(12, 4, authority.lat, border_style)
        ws.write(12, 5, authority.lng, border_style)
        ws.write(12, 6, authority.parentId, border_style)
        ws.write(12, 7, authority.address, border_style)

        ws.write(14, 0, u'ผู้ใช้งาน', bold_style)
        ws.write(15, 0, u'บัญชีผู้ใช้งาน (กรณีมีอยู่แล้ว)', header_style)
        ws.write(15, 1, u'ชื่อ', header_style)
        ws.write(15, 2, u'นามสกุล', header_style)
        ws.write(15, 3, u'เลขที่บัตรประจำตัวประชาชน', header_style)
        ws.write(15, 4, u'เบอร์โทรศัพท์', header_style)
        ws.write(15, 5, u'อีเมล', header_style)

        count = count + 1

    print count
    response = HttpResponse(content_type="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=Authorities.xls'
    
    wb.save(response)
    return response


def print_invite_code_authorities():
    print "Start..."

    wb = xlwt.Workbook()
    
    fnt = xlwt.Font()
    fnt.bold = True

    al = xlwt.Alignment()
    al.horz = xlwt.Alignment.HORZ_CENTER

    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1

    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['gray25']

    header_style = xlwt.XFStyle()
    header_style.font = fnt
    header_style.borders = borders
    header_style.pattern = pattern
    header_style.alignment = al

    border_style = xlwt.XFStyle()
    border_style.borders = borders

    bold_style = xlwt.XFStyle()
    bold_style.font = fnt

    sheetname = 'invitation_code'
    
    ws = wb.add_sheet(sheetname)
    ws.write(0, 0, u'อำเภอ', header_style)
    ws.write(0, 1, u'ชื่อ', header_style)
    ws.write(0, 2, u'รหัสพื้นที่', header_style)
    ws.write(0, 3, u'หมดอายุเมื่อ', header_style)
    
    authorities = Authority.objects.all()

    AUTHORITY_ROW = 1
    for authority in authorities:
        if authority.inherits.count() and u'อำเภอ' in authority.inherits.all()[0].name:
            ws.write(AUTHORITY_ROW, 0, authority.inherits.all()[0].name, border_style)
            ws.write(AUTHORITY_ROW, 1, authority.name, border_style)
            ws.write(AUTHORITY_ROW, 2, authority.invite.code, border_style)

            expired_at = authority.invite.expired_at
            ws.write(AUTHORITY_ROW, 3, '%s/%s/%s' % (
                    expired_at.day,
                    expired_at.month,
                    (expired_at.year + 543)
                ), border_style)

            AUTHORITY_ROW = AUTHORITY_ROW + 1

    response = HttpResponse(content_type="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=InvitationCodeAuthorities.xls'
    
    wb.save(response)
    return response


