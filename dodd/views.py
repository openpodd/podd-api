from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from dodd.tasks import create_podd_report_from_public_report

@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def test_link_report(request, report_id):
    create_podd_report_from_public_report(int(report_id))
    return HttpResponse("ok")