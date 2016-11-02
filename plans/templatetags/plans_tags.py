
from django import template
from plans.functions import plan_authority_get_level_areas

register = template.Library()

@register.simple_tag
def plan_authority_level_areas(plan, authority, level, spliter=', '):

    if not plan or not authority or not level:
        return ''

    level_areas = plan._current_log['level_areas']
    my_level_areas = plan_authority_get_level_areas(authority, level_areas)
    areas = my_level_areas.get(level) or []

    return spliter.join([a['address'] for a in areas])
