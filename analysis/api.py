import os, tempfile, zipfile
import mimetypes
import datetime

from django.conf import settings
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from common.constants import USER_STATUS_PODD

from .functions import fetch_report, dump_csv


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def export_analysis_csv(request):

    if not (request.user.is_staff or request.user.status == USER_STATUS_PODD):
        return HttpResponse('Cannot perform this action.')

    date_start = request.GET.get('dateStart')
    date_end = request.GET.get('dateEnd')

    try:
        date_start = datetime.datetime.strptime(date_start, '%Y-%m-%d')
        date_end = datetime.datetime.strptime(date_end, '%Y-%m-%d')
    except:
        return HttpResponse('Date Error.')

    reports = fetch_report(date_start, date_end)
    # print 'total count = %d' % (len(reports),)
    # for (k,v) in symptom_map.items():
    #    print "%s" % (k)
    dump_csv(reports)

    filename = "/tmp/sick_death.csv"
    download_name = "export_analysis_csv.csv"
    wrapper = FileWrapper(open(filename))
    content_type = mimetypes.guess_type(filename)[0]

    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Length'] = os.path.getsize(filename)
    response['Content-Disposition'] = 'attachment; filename=%s' % download_name
    return response
