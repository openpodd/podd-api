
from rest_framework import pagination

from reports.serializers import ReportListESSerializer, ReportListESWFormDataSerializer, ReportSerializer, \
    ReportListESLiteSerializer, AdministrationAreaContactSerializer, ReportListFullSerializer


class PaginatedReportSerializer(pagination.PaginationSerializer):
    class Meta:
        object_serializer_class = ReportSerializer


class PaginatedReportListESSerializer(pagination.PaginationSerializer):
    class Meta:
        object_serializer_class = ReportListESSerializer


class PaginatedReportListESWFormDataSerializer(pagination.PaginationSerializer):
    class Meta:
        object_serializer_class = ReportListESWFormDataSerializer


class PaginatedReportListESLiteSerializer(pagination.PaginationSerializer):
    class Meta:
        object_serializer_class = ReportListESLiteSerializer


class PaginatedAdministrationContactSerializer(pagination.PaginationSerializer):
    class Meta:
        object_serializer_class = AdministrationAreaContactSerializer


class PaginatedReportListFullSerializer(pagination.PaginationSerializer):
    class Meta:
        object_serializer_class = ReportListFullSerializer
