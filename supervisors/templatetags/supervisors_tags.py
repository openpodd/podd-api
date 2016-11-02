
from django import template

from accounts.models import User, GroupAdministrationArea
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA
from supervisors.functions import get_querystring_filter_user_status

register = template.Library()


@register.assignment_tag
def get_user_in_area(area, user_status=None):
    querystring = {
        'groups__groupadministrationarea__administration_area': area,
        'groups__type': GROUP_WORKING_TYPE_ADMINSTRATION_AREA,
    }

    querystring = get_querystring_filter_user_status(querystring, user_status)
    users = User.objects.filter(**querystring).order_by('username')
    if not user_status:
        users.exclude(status='')

    return users


@register.filter
def display_user_reportable_administration_area(user):
    areas = user.authority_users.all()

    if areas:
        return areas[0].name
    else:
        return ''
