# -*- encoding: utf-8 -*-
from datetime import datetime
from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError
from reports.models import Report, AdministrationArea


class Command(BaseCommand):
    args = 'file_path.csv'
    help = 'Import Administration Area with code from csv: file_path.csv'

    month_name = [
        u"มกราคม",
        u"กุมภาพันธ์",
        u"มีนาคม",
        u"เมษายน",
        u"พฤษภาคม",
        u"มิถุนายน",
        u"กรกฎาคม",
        u"สิงหาคม",
        u"กันยายน"
    ]

    def handle(self, *args, **options):
        amphors = AdministrationArea.objects.filter(depth=1).exclude(id__in=[1,4])
        months = [[datetime(2015, m, 1), datetime(2015, m + 1, 1), m] for m in range(1, 8)]
        for start, end, m in months:
            for amphor in amphors:
                reports_all = Report.objects.filter(Q(test_flag__isnull=True) | Q(test_flag=False))
                reports_all = reports_all.filter(created_at__gte=start,
                                                    created_at__lt=end,
                                                    administration_area__in=amphor.get_descendants())

                reports_positive = reports_all.filter(negative=False)
                reports_negative = reports_all.filter(negative=True)
                reports_sms = reports_negative.filter(Q(priority=3) | Q(priority=5))
                print '%s,%s,%d,%d,%d,%d' % (self.month_name[m - 1],
                                             amphor,
                                             reports_all.count(),
                                             reports_positive.count(),
                                             reports_negative.count(),
                                             reports_sms.count())

