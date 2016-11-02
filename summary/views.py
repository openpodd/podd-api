# -*- encoding: utf-8 -*-
import collections
import datetime
import json

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.datastructures import SortedDict

from accounts.models import User
from common.constants import PRIORITY_CHOICES, USER_STATUS_CHOICES, USER_STATUS_VOLUNTEER, \
    USER_STATUS_ADDITION_VOLUNTEER, USER_STATUS_COORDINATOR
from reports.models import Report, ReportType, ReportImage
from summary import VetReport, XlsRenderer, XlsSheet
from supervisors.functions import get_querystring_filter_user_status


def summary_report(self, summary_slug):

    # HARD CODE GET REPORT TYPE: VETERIAN
    rt = ReportType.objects.get(name=u'สัตว์แพทย์')
    reports = Report.objects.filter(type=rt)
    vr = VetReport(report_type=rt, reports=reports, topic='animalType')

    header = [
        [0, 0, 0, 14, u'รายงานจำนวนสัตว์ป่วยที่เข้ารับการรักษาในสถานพยาบาลสัตว์'],

        [1, 1, 0, 14, u'ระหว่างวันที่ 1 มกราคม - 31 ธันวาคม พ.ศ. 2553'],
        [2, 3, 0, 1, u'ชนิดสัตว์'],
        [2, 2, 2, 14, u'จำนวนตัว'],
        [3, 3, 2, 2, u'มกราคม'],
        [3, 3, 3, 3, u'กุมภา'],
        [3, 3, 4, 4, u'มีนา'],
        [3, 3, 5, 5, u'เมษา'],
        [3, 3, 6, 6, u'พฤษภา'],
        [3, 3, 7, 7, u'มิถุนา'],
        [3, 3, 8, 8, u'กรกฎา'],
        [3, 3, 9, 9, u'สิงหา'],
        [3, 3, 10, 10, u'กันยา'],
        [3, 3, 11, 11, u'ตุลา'],
        [3, 3, 12, 12, u'พฤศจิกา'],
        [3, 3, 13, 13, u'ธันวา'],
        [3, 3, 14, 14, u'รวม'],
    ]

    sheet1 = XlsSheet(data=vr.answers, sheetname=u'สสป. 1', header=header)

    # report 2
    vr = VetReport(report_type=rt, reports=reports, topic='vaccine', subtopic='animalType')
    header = [
        [0, 0, 0, 15, u'รายงานการป้องกันโรคสัตว์'],

        [1, 1, 0, 15, u'ระหว่างวันที่ 1 มกราคม - 31 ธันวาคม พ.ศ. 2553'],
        [2, 2, 0, 1, u'การป้องกัน'],
        [2, 2, 2, 15, u'จำนวนตัว'],
        [3, 3, 0, 1, u'วัคซีนป้องกันโรค'],
        [3, 3, 2, 2, u'ชนิดสัตว์'],
        [3, 3, 3, 3, u'มกราคม'],
        [3, 3, 4, 4, u'กุมภา'],
        [3, 3, 5, 5, u'มีนา'],
        [3, 3, 6, 6, u'เมษา'],
        [3, 3, 7, 7, u'พฤษภา'],
        [3, 3, 8, 8, u'มิถุนา'],
        [3, 3, 9, 9, u'กรกฎา'],
        [3, 3, 10, 10, u'สิงหา'],
        [3, 3, 11, 11, u'กันยา'],
        [3, 3, 12, 12, u'ตุลา'],
        [3, 3, 13, 13, u'พฤศจิกา'],
        [3, 3, 14, 14, u'ธันวา'],
        [3, 3, 15, 15, u'รวม'],
    ]
    sheet2 = XlsSheet(data=vr.answers, sheetname=u'สสป. 2', header=header)

    # report 3
    vr = VetReport(report_type=rt, reports=reports, topic='Medicine', subtopic='animalType')
    header = [
        [0, 0, 0, 15, u'รายงานการประกอบวิชาชีพการสัตวแพทย์ (อายุรกรรม)'],
        [1, 1, 0, 15, u'ระหว่างวันที่ 1 มกราคม - 31 ธันวาคม พ.ศ. 2553'],
        [2, 2, 0, 1, u'การรักษาทางอายุรกรรม'],
        [2, 2, 2, 15, u'จำนวนตัว'],
        [3, 3, 0, 1, u'กลุ่มอาการ/โรค'],
        [3, 3, 2, 2, u'ชนิดสัตว์'],
        [3, 3, 3, 3, u'มกราคม'],
        [3, 3, 4, 4, u'กุมภา'],
        [3, 3, 5, 5, u'มีนา'],
        [3, 3, 6, 6, u'เมษา'],
        [3, 3, 7, 7, u'พฤษภา'],
        [3, 3, 8, 8, u'มิถุนา'],
        [3, 3, 9, 9, u'กรกฎา'],
        [3, 3, 10, 10, u'สิงหา'],
        [3, 3, 11, 11, u'กันยา'],
        [3, 3, 12, 12, u'ตุลา'],
        [3, 3, 13, 13, u'พฤศจิกา'],
        [3, 3, 14, 14, u'ธันวา'],
        [3, 3, 15, 15, u'รวม'],
    ]
    sheet3 = XlsSheet(data=vr.answers, sheetname=u'สสป. 3', header=header)

    # report 4
    vr = VetReport(report_type=rt, reports=reports, topic='Surgery', subtopic='animalType')
    header = [
        [0, 0, 0, 15, u'รายงานการประกอบวิชาชีพการสัตวแพทย์ (ศัลยกรรม)'],
        [1, 1, 0, 15, u'ระหว่างวันที่ 1 มกราคม - 31 ธันวาคม พ.ศ. 2553'],
        [2, 2, 0, 1, u'การรักษาทางศัลยกรรม'],
        [2, 2, 2, 15, u'จำนวนตัว'],
        [3, 3, 0, 1, u'กลุ่มอาการ/โรค'],
        [3, 3, 2, 2, u'ชนิดสัตว์'],
        [3, 3, 3, 3, u'มกราคม'],
        [3, 3, 4, 4, u'กุมภา'],
        [3, 3, 5, 5, u'มีนา'],
        [3, 3, 6, 6, u'เมษา'],
        [3, 3, 7, 7, u'พฤษภา'],
        [3, 3, 8, 8, u'มิถุนา'],
        [3, 3, 9, 9, u'กรกฎา'],
        [3, 3, 10, 10, u'สิงหา'],
        [3, 3, 11, 11, u'กันยา'],
        [3, 3, 12, 12, u'ตุลา'],
        [3, 3, 13, 13, u'พฤศจิกา'],
        [3, 3, 14, 14, u'ธันวา'],
        [3, 3, 15, 15, u'รวม'],
    ]
    sheet4 = XlsSheet(data=vr.answers, sheetname=u'สสป. 4', header=header)

    # report 5
    vr = VetReport(report_type=rt, reports=reports, topic='infectious')
    header = [
        [0, 0, 0, 14, u'รายงานการเกิดโรคระบาดสัตว์ (Infectious Diseases)'],
        [1, 1, 0, 14, u'ระหว่างวันที่ 1 มกราคม - 31 ธันวาคม พ.ศ. 2553'],
        [2, 3, 0, 1, u'โรคระบาดสัตว์'],
        [2, 2, 2, 14, u'จำนวนตัว'],
        [3, 3, 2, 2, u'มกราคม'],
        [3, 3, 3, 3, u'กุมภา'],
        [3, 3, 4, 4, u'มีนา'],
        [3, 3, 5, 5, u'เมษา'],
        [3, 3, 6, 6, u'พฤษภา'],
        [3, 3, 7, 7, u'มิถุนา'],
        [3, 3, 8, 8, u'กรกฎา'],
        [3, 3, 9, 9, u'สิงหา'],
        [3, 3, 10, 10, u'กันยา'],
        [3, 3, 11, 11, u'ตุลา'],
        [3, 3, 12, 12, u'พฤศจิกา'],
        [3, 3, 13, 13, u'ธันวา'],
        [3, 3, 14, 14, u'รวม'],
    ]
    sheet5 = XlsSheet(data=vr.answers, sheetname=u'สสป. 5', header=header)

    # report 6
    vr = VetReport(report_type=rt, reports=reports, topic='zoonosis', subtopic='animalType')
    header = [
        [0, 0, 0, 15, u'รายงานการเกิดโรคติดต่อระหว่างสัตว์และคน (Zoonosis)'],
        [1, 1, 0, 15, u'ระหว่างวันที่ 1 มกราคม - 31 ธันวาคม พ.ศ. 2553'],
        [2, 3, 0, 1, u'โรคติดต่อระหว่างสัตว์และคน'],
        [2, 2, 2, 15, u'จำนวนตัว'],
        [3, 3, 2, 2, u'ชนิดสัตว์'],
        [3, 3, 3, 3, u'มกราคม'],
        [3, 3, 4, 4, u'กุมภา'],
        [3, 3, 5, 5, u'มีนา'],
        [3, 3, 6, 6, u'เมษา'],
        [3, 3, 7, 7, u'พฤษภา'],
        [3, 3, 8, 8, u'มิถุนา'],
        [3, 3, 9, 9, u'กรกฎา'],
        [3, 3, 10, 10, u'สิงหา'],
        [3, 3, 11, 11, u'กันยา'],
        [3, 3, 12, 12, u'ตุลา'],
        [3, 3, 13, 13, u'พฤศจิกา'],
        [3, 3, 14, 14, u'ธันวา'],
        [3, 3, 15, 15, u'รวม'],
    ]
    sheet6 = XlsSheet(data=vr.answers, sheetname=u'สสป. 6', header=header)

    xls = XlsRenderer(filename='Vet Report')
    xls.add_sheet(sheet1)
    xls.add_sheet(sheet2)
    xls.add_sheet(sheet3)
    xls.add_sheet(sheet4)
    xls.add_sheet(sheet5)
    xls.add_sheet(sheet6)
    return xls.run()


def summary_report_for_monitor(request):

    dates = request.GET.get('dates')
    offset = request.GET.get('offset')
    try:
        date_range = dates.split('-')
        date_start = datetime.datetime.strptime(date_range[0], "%d/%m/%Y") 
        date_end = datetime.datetime.strptime(date_range[1], "%d/%m/%Y") 
        if offset:
            offset_timezone = int(offset)
        else:
            offset_timezone = 0
    except:
        return HttpResponse("Date Error.");

    else:
        results = SortedDict()
        header = [
            [0, 0, 0, 0, u'id'],
            [0, 0, 1, 1, u'negative'],
            [0, 0, 2, 2, u'flag'],
            [0, 0, 3, 3, u'type'],
            [0, 0, 4, 4, u'animal_type'],
            [0, 0, 5, 5, u'date'],
            [0, 0, 6, 6, u'sick'],
            [0, 0, 7, 7, u'death'],
            [0, 0, 8, 8, u'total'],
            [0, 0, 9, 9, u'administration_area'],
            [0, 0, 10, 10, u'parent_name'],
            [0, 0, 11, 11, u'reporter'],
            [0, 0, 12, 12, u'report_location_latitude'],
            [0, 0, 13, 13, u'report_location_longitude'],
            [0, 0, 14, 14, u'administration_area_location_latitude'],
            [0, 0, 15, 15, u'administration_area_location_longitude'],
        ]
        
        reports = Report.objects.filter(negative=True, test_flag=False, parent__isnull=True, date__gte=date_start + datetime.timedelta(hours=-offset_timezone), date__lt=date_end + datetime.timedelta(days=1, hours=-offset_timezone)).order_by('id')
        for report in reports:

            if report.administration_area.get_parent():
                parent_name = report.administration_area.get_parent().name
            else:
                parent_name = ''

            if report.administration_area:
                administration_area_location_latitude = report.administration_area.location[1]
                administration_area_location_longitude = report.administration_area.location[0]
            else:
                administration_area_location_latitude = ''
                administration_area_location_longitude = ''

            if report.report_location:
                report_location_latitude = report.report_location[1]
                report_location_longitude = report.report_location[0]
            else:
                report_images = ReportImage.objects.filter(report_id=report.id).exclude(location=None)
                if report_images.count() > 0:
                    report_location_latitude = report_images[0].location[1]
                    report_location_longitude = report_images[0].location[0]
                else:
                    report_location_latitude = ''
                    report_location_longitude = ''

            form_data = json.loads(report.form_data)

            try:
                animal_type = form_data['animalType']
            except:
                animal_type = ''

            try:
                sick = form_data['sickCount']
            except:
                sick = ''

            try:
                death = form_data['deathCount']
            except:
                death = ''

            try:
                total = form_data['totalCount']
            except:
                total = ''

            item = {
                'id': report.id,
                'negative': report.negative,
                'flag': PRIORITY_CHOICES[report.priority-1][1] if report.priority else '-',
                'type': report.type.name,
                'animal_type': animal_type,
                'date': (report.date + datetime.timedelta(hours=offset_timezone)).strftime('%d-%m-%Y'),
                'sick': sick,
                'death': death,
                'total': total,
                'administration_area': report.administration_area.name.replace(' ', ''),
                'parent_name': parent_name,
                'reporter': report.created_by.get_full_name(),
                'report_location_latitude': report_location_latitude,
                'report_location_longitude': report_location_longitude,
                'administration_area_location_latitude': administration_area_location_latitude,
                'administration_area_location_longitude': administration_area_location_longitude,
            }

            results[report.id] = {}
            results[report.id]['key'] = 4
            results[report.id]['answers'] = item

        sheet1 = XlsSheet(data=results, sheetname=u'รายละเอียดรายงาน', header=header)

        xls = XlsRenderer(filename='Monitor Report')
        xls.add_sheet(sheet1)
        return xls.run()


def summary_list_volunteer(request):
    if request.GET and request.GET['status']:
        query = request.GET['status'].replace('-', '_')

        status_with_full_table = (
            USER_STATUS_VOLUNTEER,
            USER_STATUS_ADDITION_VOLUNTEER,
            USER_STATUS_COORDINATOR,
            'additional_volunteer',
        )

        results = {}
        if query.lower() in status_with_full_table:
            header = [
                [0, 0, 0, 0, u'อำเภอ'],
                [0, 0, 1, 1, u'อปท.'],
                [0, 0, 2, 2, u'รายชื่อ'],
                [0, 0, 3, 3, u'ที่อยู่'],
                [0, 0, 4, 4, u'เบอร์ติดต่อในโครงการ'],
                [0, 0, 5, 5, u'เบอร์ติดต่อ'],
                [0, 0, 6, 6, u'ชื่อบัญชีผู้ใช้'],
                [0, 0, 7, 7, u'รหัสผ่าน'],
                [0, 0, 8, 8, u'Serial Number(IMEI)'],
            ]
        else:
            header = [
                [0, 0, 0, 0, u'รายชื่อ'],
                [0, 0, 1, 1, u'ที่อยู่'],
                [0, 0, 2, 2, u'เบอร์ติดต่อ'],
                [0, 0, 3, 3, u'ชื่อบัญชีผู้ใช้'],
                [0, 0, 4, 4, u'รหัสผ่าน'],
            ]

        status_from_query_params = request.GET['status']
        querystring = get_querystring_filter_user_status(None, status_from_query_params)

        users = User.objects.filter(**querystring).order_by('administration_area')
        for user in users:

            if user.administration_area and user.administration_area.get_parent():
                parent_area_name = user.administration_area.get_parent().name
            else:
                parent_area_name = ''

            if user.administration_area:
                area_name = user.administration_area.name
            else:
                area_name = ''

            areas = user.authority_users.all()
            if area_name == '' and areas.count():
                area_name = areas[0].name

            item = {
                u'อำเภอ': parent_area_name,
                u'อปท.': area_name,
                u'รายชื่อ': user.get_full_name(),
                u'ที่อยู่': user.contact,
                u'เบอร์ติดต่อในโครงการ': user.project_mobile_number,
                u'เบอร์ติดต่อ': user.telephone,
                u'ชื่อบัญชีผู้ใช้': user.username,
                u'รหัสผ่าน': user.display_password,
                u'Serial Number(IMEI)': user.serial_number,
            }

            results[user.username] = {}
            results[user.username]['key'] = 4
            results[user.username]['answers'] = item

            results = collections.OrderedDict(sorted(results.items()))
            
        sheet1 = XlsSheet(data=results, sheetname=u'รายชื่อ', header=header)

        xls = XlsRenderer(filename=query)
        xls.add_sheet(sheet1)
        return xls.run()
    else:
        return HttpResponse("status. status is required")
