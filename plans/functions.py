

def plan_get_level_areas(my_areas, level_areas):
    my_level_areas = {}

    for level, areas in level_areas.iteritems():
        for area in areas:
            for my_area in my_areas:
                if my_area.id == area['id']:

                    if not my_level_areas.get(level):
                        my_level_areas[level] = []

                    my_level_areas[level].append(area)

    return my_level_areas


def plan_authority_get_level_areas(authority, level_areas):

    from reports.models import AdministrationArea

    my_areas = AdministrationArea.objects.filter(authority__id=authority.id)
    return plan_get_level_areas(my_areas, level_areas)



def plan_user_get_level_areas(user, level_areas):

    from reports.models import AdministrationArea

    my_areas = AdministrationArea.objects.filter(authority__users=user)
    return plan_get_level_areas(my_areas, level_areas)