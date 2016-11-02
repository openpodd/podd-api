
from django.db.models import Q

from accounts.models import Configuration, UserDevice, NearbyArea
from common.constants import NEWS_TYPE_ADMINISTRATION_AREA
from common.pub_tasks import publish
from notifications.functions import create_notification

def publish_news(news):
    try:
        enabled_system = Configuration.objects.get(system='web.news.enabled', key=news.type, value='True')
        gcm_api_key = Configuration.objects.get(system='android.server.push_notification', key='GCM_API_KEY')
    except Configuration.DoesNotExist:
        return

    devices = UserDevice.objects.exclude(gcm_reg_id=None, apns_reg_id=None)
    # QUESTION: SEND NEWS TO BOTH REPORTER AND PROSPECTOR ??

    # CHECK TYPE
    if news.area:
    # if news.area and news.type == NEWS_TYPE_ADMINISTRATION_AREA:
        areas = [news.area]
        areas.extend(list(news.area.get_descendants()))

        devices = devices.filter(
            Q(user__groups__groupadministrationarea__administration_area__in=areas) | Q(user__is_staff=True)
        )
    '''
    elif news.area and news.type == NEWS_TYPE_NEARBY_AREA:
        areas = [news.area]
        try:
            area = NearbyArea.objects.get(area=news.area)
        except NearbyArea.DoesNotExist:
            pass
        else:
            areas.extend(list(area.neighbors.all()))

        devices = devices.filter(
            Q(user__groups__groupadministrationarea__administration_area__in=areas) | Q(user__is_staff=True)
        )
    '''
    for device in devices:
        notification = create_notification(report=None, receive_user=device.user, message=news.message, message_type=news.type.lower())

    gcm_registration_ids = devices.values_list('gcm_reg_id', flat=True)

    ## Deprecated
    ## Move to notification.save()
    #publish('news:new', {
    #    'GCMAPIKey': gcm_api_key.value,
    #    'androidRegistrationIds': list(gcm_registration_ids),
    #    'type': news.type.lower(),
    #    'message': news.message,
    #})
