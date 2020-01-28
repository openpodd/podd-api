from django.db.models import Q

from accounts.models import UserDevice
from common.constants import NEWS_TYPE_NEWS
from common.functions import publish_gcm_message, publish_apns_message


def publish_news(news):
    devices = UserDevice.objects.exclude(gcm_reg_id=None, apns_reg_id=None)

    # CHECK TYPE
    if news.area:
        areas = [news.area]
        areas.extend(list(news.area.get_descendants()))

        devices = devices.filter(
            Q(user__groups__groupadministrationarea__administration_area__in=areas) | Q(user__is_staff=True)
        )

    for device in devices:
        if device.gcm_reg_id:
            publish_gcm_message([device.gcm_reg_id], news.message, NEWS_TYPE_NEWS)
        if device.apns_reg_id:
            publish_apns_message([device.apns_reg_id], news.message)
