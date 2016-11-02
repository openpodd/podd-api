# -*- encoding: utf-8 -*-

import xlwt

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group

from accounts.models import User, GroupAdministrationArea, Authority
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA, GROUP_WORKING_TYPE_REPORT_TYPE
from common.factory import randnum, randstr
from reports.models import AdministrationArea


class Command(BaseCommand):
    help = 'Migrate user to authority'

    def handle(self, *args, **options):
        print "Start..."
        
        for user in User.objects.order_by('id'):

            group_administration_areas = user.groups.filter(type=GROUP_WORKING_TYPE_ADMINSTRATION_AREA).order_by('id')
            administration_areas = AdministrationArea.objects.filter(groupadministrationarea__group__in=group_administration_areas)
            
            if not administration_areas.count() == 1:
                continue

            administration_area = administration_areas[0]
            if not administration_area.is_leaf():
                continue

            name = administration_area.name
            code = administration_area.code

            try:
                authority = Authority.objects.get(code=code)
                authority.add_user(user)

            except Authority.DoesNotExist:
                print "create authority: %s" % name
                authorities = Authority(name=name, code=code)
                authorities.administration_areas.add(administration_area)
                authorities.user.add(user)

            print "success migrate user to authority: %s" % user.id
        
        print "Finish..."
