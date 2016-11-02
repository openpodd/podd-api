from django.core.management import BaseCommand
from flags.models import Flag
from reports.models import Report

class Command(BaseCommand):

    help = 'Update lastest flag'

    def handle(self, *args, **options):

        for report in Report.objects.filter(negative=True):
            flags = Flag.objects.filter(comment__report=report)
            if flags.exists():
                report_lastest_flag = flags.latest('id')
                report.priority = report_lastest_flag.priority
                report.save()
