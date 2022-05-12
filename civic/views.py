from django.conf import settings
from django.core.paginator import Paginator
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from reports.models import Report
from reports.paginations import PaginatedReportSerializer


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def list_civic_report(request, status):
    page_size = request.QUERY_PARAMS.get('page_size') or 20
    page = request.QUERY_PARAMS.get('page') or 1
    user = request.user
    authority = user.get_my_authority()
    queryset = Report.objects.filter(administration_area__authority=authority,
                                     type__code=settings.CIVIC_REPORT_TYPE_CODE,
                                     state__code=status)
    pagination_serializer_class = PaginatedReportSerializer
    paginator = Paginator(queryset, page_size)
    reports = paginator.page(page)
    serializer = pagination_serializer_class(reports)
    return Response(serializer.data)