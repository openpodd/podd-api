import json

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from accounts.models import Authority, UserDevice, Configuration
from common.constants import NEWS_TYPE_NEWS
from common.pub_tasks import publish
from reports.models import Report


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def broadcast_via_gcm(request):
    # Validate here
    post_data = request.POST

    report_id = post_data.get('report_id')
    message = post_data.get('message')

    if not report_id:
        return HttpResponseBadRequest(json.dumps({'details': 'report_id field is required'}), content_type='application/json')

    try:
        report = Report.objects.get(pk=report_id)
    except Report.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({'details': 'report_id field is not valid'}), content_type='application/json')

    authority = report.administration_area.authority
    if not authority.user_can_edit(request.user):
        return HttpResponseForbidden(json.dumps({'details': 'Forbidden: You can not broadcast to this authority'}),
                                     content_type='application/json')

    if not message or len(message) == 0:
        return HttpResponseBadRequest(json.dumps({'details': 'message field is not valid'}),
                                      content_type='application/json')

    try:
        gcm_api_key = Configuration.objects.get(system='android.server.push_notification', key='GCM_API_KEY')
    except Configuration.DoesNotExist:
        gcm_api_key = Configuration()
        gcm_api_key.value = ''

    users = authority.users.all()
    for user in users:
        # Do not broadcast to reporter.
        if report.created_by.id == user.id:
            continue

        try:
            device = UserDevice.objects.get(user=user)
        except UserDevice.DoesNotExist:
            continue

        if device.gcm_reg_id:
            publish('news:new', {
                'GCMAPIKey': gcm_api_key.value,
                'androidRegistrationIds': [device.gcm_reg_id],
                'type': NEWS_TYPE_NEWS,
                'message': message,
                'reportId': report_id
            })

        if device.apns_reg_id:
            publish('news:new', {
                'apnsRegistrationIds': [device.apns_reg_id],
                'type': NEWS_TYPE_NEWS,
                'message': message,
                'reportId': report_id
            })

    return HttpResponse(json.dumps({'status': 'OK'}), content_type='application/json')
