# -*- encoding: utf-8 -*-
import datetime
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from animal.models import AnimalRecord

from animal.serializers import AnimalRecordCreateSerializer, AnimalRecordDeleteSerializer, AnimalRecordMarkDeathSerializer, AnimalRecordUpdateSerializer
import csv
from django.http import HttpResponse


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


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="animal_records.csv"'

    writer = csv.writer(response)
    writer.writerow(['id',
                     'วันที่',
                     'พื้นที่',
                     'ชื่อเจ้าของ',    
                     'เลขบัตรประชาชน',
                     'เบอร์โทรศัพท์',
                     'บ้านเลขที่',
                     'หมู่ที่',
                     'แขวง/ตำบล',
                     'ซอย',
                     'ถนน',
                     'ประเภทสัตว์',
                     'ชื่อสัตว์'
                     'สี',
                     'เพศ',
                     'วัคซีน',
                     'วันที่ฉีดล่าสุด',
                     'ประวัติวัคซีนอื่นๆ',
                     'การคุมกำเนิด',
                     'การคุมกำเนิด อื่นๆ',
                     'อายุ ปี',
                     'อายุ เดือน',
                     'วันเดือนปีเกิด',
                     'latitude',
                     'longitude',
                     'ชื่อผู้รายงาน',
                     'สถานะสัตว์(แสดง/ไม่แสดง)',
                     'สถานะสัตว์(มีชีวิต/ไม่มีชีวิต)',
                     'วันที่ปรับสถานะเสียชีวิต',
                     'ผู้ที่ปรับสถานะเสียชีวิต',
                     'วันที่อัปเดตล่าสุด',
                     ])

    for record in records:
        current_date = datetime.date.today()
        birth_date = current_date - datetime.timedelta(days=record.age_year*365 + record.age_month*30)
        deleted = 'ไม่แสดง' if record.deleted_date else 'แสดง'
        status = 'มีชีวิต' if not record.death_updated_date else 'เสียชีวิต'

        writer.writerow([record.id, 
                         record.created_at,
                         record.authority.name.encode("utf-8"),
                         record.name.encode("utf-8"), 
                         record.national_id.encode("utf-8"),
                         record.phone.encode("utf-8"),
                         record.addr_no.encode("utf-8"),
                         record.addr_moo.encode("utf-8"),
                         record.addr_subdistrict.encode("utf-8"),
                         record.addr_soi.encode("utf-8"),
                         record.addr_road.encode("utf-8"),
                         record.animal_type.encode("utf-8"),
                         record.animal_name.encode("utf-8"),
                         record.animal_color.encode("utf-8"),
                         record.animal_gender.encode("utf-8"),
                         record.vaccine.encode("utf-8"),
                         record.last_vaccine_date if record.vaccine == 'เคย' else "",
                         record.vaccine_other.encode("utf-8") if record.vaccine_other else "",
                         record.spay.encode("utf-8"),
                         record.spay_other.encode("utf-8") if record.spay_other else "",
                         record.age_year,
                         record.age_month,
                         birth_date,
                         record.latitude,
                         record.longitude,
                         record.updated_by.encode("utf-8"),
                         deleted,
                         status,
                         record.death_updated_date,
                         record.death_updated_by.encode("utf-8") if record.death_updated_by else "",
                         record.updated_at,
                         ])

    return response
    
