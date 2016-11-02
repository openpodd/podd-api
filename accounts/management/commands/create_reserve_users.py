# -*- encoding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from accounts.models import GroupAdministrationArea, User
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA, USER_STATUS_ADDITION_VOLUNTEER
from common.factory import randnum
from reports.models import AdministrationArea


class Command(BaseCommand):
    help = 'Create 2 reserve users for every leaf area'

    def handle(self, *args, **options):

        areas = []
        for area in AdministrationArea.objects.exclude(code=''):
            if area.is_leaf():
                areas.append(area)

        for area in areas:
            try:
                group = GroupAdministrationArea.objects.get(
                    administration_area=area,
                    group__type=GROUP_WORKING_TYPE_ADMINSTRATION_AREA,
                )
            except:
                return

            code = group.administration_area.code
            total_users_in_group = group.group.user_set.count()

            for i in range(1, 3):
                username = 'podd.%s.%02d' % (code, total_users_in_group+i)
                password = '%06d' % randnum()

                user = User.objects.create_user(
                    username=username,
                    password=password,
                    administration_area=group.administration_area,
                    display_password=password,
                    status=USER_STATUS_ADDITION_VOLUNTEER,
                )

                user.groups.add(group.group)

                print 'Created %s,%s' % (username, password)
