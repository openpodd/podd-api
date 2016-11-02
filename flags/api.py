from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, link, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import GroupReportType, GroupAdministrationArea
from common.constants import (PRIORITY_IGNORE, PRIORITY_CASE,
    GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE, GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA,
    USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER)
from common.functions import (has_permission_on_report_type, has_permission_on_administration_area,
    filter_permitted_administration_areas_and_descendants, get_administration_area_and_ancestors_ids)
from flags.functions import create_flag_comment
from flags.models import Flag
from flags.serializers import FlagSerializer
from logs.models import LogItem
from reports.models import Report
from reports.pub_tasks import publish_report_flag
from reports.tasks import send_alert_new_case


# Deprecate
class FlagViewSet(viewsets.ModelViewSet):
    model = Flag
    serializer_class = FlagSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    ordering_fields = ('-created_at', )

    def get_queryset(self):
        return Flag.objects.all()

    def list(self, request):
        queryset = self.get_queryset().order_by('-created_at')
        report_id = request.QUERY_PARAMS.get('reportId')

        if report_id:
            queryset = queryset.filter(comment__report__id=report_id)

        if request.QUERY_PARAMS.get('page_size'):
            queryset = queryset[:request.QUERY_PARAMS.get('page_size')]

        serializer = FlagSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        flag = get_object_or_404(queryset, pk=pk)

        if (has_permission_on_report_type(user=request.user, report_type=flag.comment.report.type) and \
            has_permission_on_administration_area(user=request.user, administration_area=flag.comment.report.administration_area)):
            serializer = FlagSerializer(flag)
            return Response(serializer.data)
        else:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

    def create(self, request):
        serializer = FlagSerializer(data=request.DATA)
        report = get_object_or_404(Report, id=request.DATA.get('reportId'))

        if serializer.is_valid():

            if (has_permission_on_report_type(user=request.user, report_type=report.type) and \
                has_permission_on_administration_area(user=request.user, administration_area=report.administration_area)):

                priority = int (request.DATA.get('priority', 0))

                # VALIDATE PERMISSON ON CHANGE FLAG TO `CASE`
                area_ids = get_administration_area_and_ancestors_ids(report.administration_area)

                if priority == PRIORITY_CASE and (
                    # GroupReportType.objects.filter(group__user=request.user,
                    #     report_type=report.type,
                    #     group__type=GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE) and \
                    # GroupAdministrationArea.objects.filter(group__user=request.user,
                    #     administration_area__in=area_ids,
                    #     group__type=GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA)):
                    request.user.status in (USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER,)):
                    return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

                comment = create_flag_comment(report=report, priority=serializer.object.priority, flag_owner=request.user)

                serializer.object.comment = comment
                serializer.object.flag_owner = request.user
                serializer.save()

                # IF FLAG PRIORITY IS IGNORE (1), WILL SET REPORT NEGATIVE to False
                if priority == PRIORITY_IGNORE:
                    report.negative = False
                elif not report.negative:
                    report.negative = True

                # IF FLAG PRIORITY IS CASE (5), WILL SEND EMAIL TO ALERT_CASE GROUP
                # ELSE, WILL RESET REPORT PARENT
                if priority == PRIORITY_CASE:
                    pass
                    # Move to notification template condition
                    # send_alert_new_case.delay(serializer.object)
                else:
                    report.parent = None

                report.save()

                LogItem.objects.log_action(key='REPORT_FLAG_CHANGE',
                    created_by=request.user, object1=report,
                    object2=serializer.object)
                publish_report_flag(serializer.data)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({u'detail': u'You do not have permission to perform this action.'},
                        status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        return Response({"detail": "Method 'PUT' not allowed."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, pk=None):
        return Response({"detail": "Method 'DELETE' not allowed."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)
