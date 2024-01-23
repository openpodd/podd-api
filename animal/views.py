# -*- encoding: utf-8 -*-
import datetime
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from animal.models import AnimalRecord

from animal.serializers import AnimalRecordCreateSerializer, AnimalRecordDeleteSerializer, AnimalRecordMarkDeathSerializer, AnimalRecordUpdateSerializer
from django.http import HttpResponse
import xlwt


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def create_animal_record(request):
    print("hello")
    serializer = AnimalRecordCreateSerializer(data=request.DATA)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response({'success': False, 'message': serializer.errors}, status=400)



@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def update_animal_record(request, animal_id):
    try:
        animal_record = AnimalRecord.objects.get(pk=animal_id)
    except AnimalRecord.DoesNotExist:
        return Response({'success': False, 'message': 'Animal record not found'}, status=404)
    
    serializer = AnimalRecordUpdateSerializer(animal_record, data=request.DATA, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response({'success': False, 'message': serializer.errors}, status=400)



@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def delete_animal_record(request, animal_id):
    try:
        animal_record = AnimalRecord.objects.get(pk=animal_id)
    except AnimalRecord.DoesNotExist:
        return Response({'success': False, 'message': 'Animal record not found'}, status=404)
    
    serializer = AnimalRecordDeleteSerializer(animal_record, data=request.DATA, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response({'success': False, 'message': serializer.errors}, status=400)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def mark_death_animal_record(request, animal_id):
    try:
        animal_record = AnimalRecord.objects.get(pk=animal_id)
    except AnimalRecord.DoesNotExist:
        return Response({'success': False, 'message': 'Animal record not found'}, status=404)
    
    serializer = AnimalRecordMarkDeathSerializer(animal_record, data=request.DATA, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response({'success': False, 'message': serializer.errors}, status=400)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def export_animal_record(request):
    user = request.user

    records = AnimalRecord.objects.filter(authority__in=user.authority_users.all()).prefetch_related("authority")

    data = []
    for record in records:
        age_year = record.age_year
        age_month = record.age_month
        current_date = datetime.date.today()
        birth_date_str = ""
        if record.birth_date:
            # calculate age year, month from birth_date
            diff = current_date - record.birth_date
            age_year = diff.days / 365
            age_month = (diff.days % 365) / 30
            if age_year == 0 and age_month == 0:
                age_month = 1
            birth_date_str = record.birth_date.strftime('%d/%m/%Y')

        deleted = u'ไม่แสดง' if record.deleted_date else u'แสดง'
        status = u'มีชีวิต' if not record.death_updated_date else u'เสียชีวิต'
        data.append([
            record.id,
            record.created_at.strftime('%d/%m/%Y %H:%M:%S'),            
            record.authority.name,
            record.name,
            record.national_id,
            record.phone,
            record.addr_no,
            record.addr_moo,
            record.addr_subdistrict,
            record.addr_soi,
            record.addr_road,
            record.animal_type,
            record.animal_name,
            record.animal_color,
            record.animal_gender,
            record.vaccine,
            record.last_vaccine_date.strftime('%d/%m/%Y') if record.vaccine == u'เคยฉีด' else "",
            record.vaccine_other if record.vaccine_other else "",
            record.spay,
            record.spay_other if record.spay_other else "",
            age_year,
            age_month,
            record.raising,
            record.raising_place,
            birth_date_str,
            record.latitude,
            record.longitude,
            record.created_by,
            deleted,
            status,
            record.death_updated_date.strftime('%d/%m/%Y') if record.death_updated_date else "",
            record.death_updated_by if record.death_updated_by else "",
            record.updated_at.strftime('%d/%m/%Y %H:%M:%S'),
            record.updated_by
        ])
        
    workbook = xlwt.Workbook(encoding='utf-8')
    sheet = workbook.add_sheet('Animal Records')
    labels = [
        u'ID',
        u'วันที่',
        u'อปท.',
        u'ชื่อเจ้าของ',
        u'เลขบัตรประชาชน',
        u'เบอร์โทรศัพท์',
        u'บ้านเลขที่',
        u'หมู่ที่',
        u'แขวง/ตำบล',
        u'ซอย',
        u'ถนน',
        u'ประเภทสัตว์',
        u'ชื่อสัตว์',
        u'สี',
        u'เพศ',
        u'ประวัติการฉีดวัคซีน',
        u'วัคซีนครั้งล่าสุด',
        u'ประวัติวัคซีนอื่นๆ',
        u'การทำหมัน',
        u'การทำหมัน อื่นๆ',
        u'อายุ ปี',
        u'อายุ เดือน',
        u'ลักษณะการเลี้ยง',
        u'สถานที่เลี้ยง',
        u'วันเดือนปีเกิด',
        u'latitude',
        u'longitude',
        u'ชื่อผู้รายงาน',
        u'สถานะสัตว์(แสดง/ไม่แสดง)',
        u'สถานะสัตว์(มีชีวิต/ไม่มีชีวิต)',
        u'วันที่ปรับสถานะเสียชีวิต',
        u'ผู้ที่ปรับสถานะเสียชีวิต',
        u'วันที่อัปเดตล่าสุด',
        u'ผู้แก้ไขข้อมูลล่าสุด'
    ]

    for col, label in enumerate(labels):
        sheet.write(0, col, label)

    # loop through all the data
    row = 1
    for item in data:
        col = 0
        for i in item:
            sheet.write(row, col, i)
            col += 1
        row += 1


    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="animal_records.xls"'
    workbook.save(response)

    return response
    
