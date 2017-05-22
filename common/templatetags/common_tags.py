import datetime
from django import template
from django.conf import settings
from common.models import Domain

register = template.Library()

@register.filter
def timezone_vary(value):

    if not value or type(value) != datetime.datetime:
        return value

    timezone = 7.0
    try:
        current_domain = Domain.objects.get(id=settings.CURRENT_DOMAIN_ID)
        timezone = current_domain.timezone
    except Domain.DoesNotExist:
        pass

    return value + datetime.timedelta(hours=timezone)