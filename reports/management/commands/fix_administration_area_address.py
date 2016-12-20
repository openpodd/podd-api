# -*- encoding: utf-8 -*-
import re

from django.core.management import BaseCommand

from reports.models import AdministrationArea


class Command(BaseCommand):
    args = '<domain_id domain_id ...>'
    help = 'Fix address that does not contain authority name'

    def handle(self, *args, **options):
        if len(args) > 0:
            for domain_id in args:
                administrationAreaList = AdministrationArea.objects.filter(
                    domain_id=domain_id,
                    code__startswith='baan',
                )

                total = administrationAreaList.count()
                done = 0

                for item in administrationAreaList:
                    done += 1
                    print "[ %d / %d ] %s .." % (done, total, item.address),

                    # Check current address, if already contains amphor skip
                    if re.search(u'อำเภอ', item.address):
                        print ' skip.'
                        continue

                    authority = item.authority
                    if authority:
                        item.address = item.address + " " + item.authority.name

                        if authority.inherits.all().count() > 0:
                            item.address = item.address + " " + authority.inherits.first().name

                        item.save()
                        print ' done.'



                print "-----------------------------------"
                print "[Done] Fixed for domain id : %s" % (domain_id, )
                print "-----------------------------------\n"
