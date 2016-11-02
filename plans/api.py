import json
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator, EmptyPage
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.functions import filter_permitted_administration_areas_and_descendants
from plans.models import Plan, PlanReport
from plans.serializers import PlanSerializer, PlanReportSerializer


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    model = Plan
    serializer_class = PlanSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        queryset = Plan.objects.all().order_by('id')
        return queryset


class PlanReportViewSet(viewsets.ReadOnlyModelViewSet):
    model = PlanReport
    serializer_class = PlanReportSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):

        user = self.request.user
        if user.is_staff:
            queryset = PlanReport.objects.order_by('-id')
        else:
            queryset = PlanReport.objects.filter(areas__in=filter_permitted_administration_areas_and_descendants(user, subscribes=True))
            queryset = queryset.order_by('-id').distinct('id')

        return queryset


    @action()
    def notify(self, request, pk, *args, **kwargs):

        from reports.models import AdministrationArea

        contacts = request.DATA.get('contacts')
        area = request.DATA.get('area')
        save = request.DATA.get('save')
        append = request.DATA.get('append')

        if not contacts or not area:
            return Response({'success': False, 'error': 'required contacts and area'})

        area = AdministrationArea.objects.get(id=area)
        old_contacts = area.contacts or ''
        area.contacts = contacts

        self.object = self.get_queryset().get(pk=pk)
        self.object.notify(area)

        if save:
            if append:
                area.contacts = old_contacts + ',' + contacts
            area.save()
            # also save to snapshot
            log = json.loads(self.object.log)
            for level_code, level_areas in log['level_areas'].iteritems():
                for level_area in level_areas:
                    if level_area['id'] == area.id:
                        level_area['contacts'] = area.contacts

            self.object.log = json.dumps(log)
            self.object.save()

        serializer = self.get_serializer(self.object)
        return Response({'success': True})


    def list(self, request):
        queryset = self.get_queryset()

        page_size = request.QUERY_PARAMS.get('page_size') or 20
        paginator = Paginator(queryset, page_size)
        page = request.QUERY_PARAMS.get('page')

        try:
            plan_reports = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            plan_reports = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver empty results.
            plan_reports = []

        serializer = self.get_serializer(plan_reports, many=True)
        return Response(serializer.data)
