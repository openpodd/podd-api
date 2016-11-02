import json
from django.core.management import BaseCommand
from django.template import Template, Context
import sys
from reports.models import Report

class Command(BaseCommand):
    help = 'Render each report form data and save back to DB'

    def handle(self, *args, **options):
        reports = Report.objects.filter(negative=True)
        total_reports = reports.count()

        done_reports_count = 0

        for report in reports:
            report_type = report.type
            template = report_type.django_template
            form_data = json.loads(report.form_data)
            t = Template(template)
            c = Context(form_data)
            report.rendered_form_data = t.render(c)
            report.save()

            done_reports_count += 1

            percent_progress = min((float(done_reports_count) / float(total_reports)) * 100, 100)
            sys.stdout.write('\r[%s] %s%% (%s/%d)' %
                             (('#' * int(percent_progress / 2)).ljust(50, ' '), int(percent_progress),
                              str(done_reports_count).rjust(10, ' '), total_reports))
            sys.stdout.flush()

