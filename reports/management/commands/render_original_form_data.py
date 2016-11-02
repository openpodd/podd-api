import json
from django.core.management import BaseCommand
from django.template import Template, Context
import sys
from reports.models import Report
from reports.search_indexes import ReportIndex


class Command(BaseCommand):
    help = 'Render each report form data and save back to DB'

    def handle(self, *args, **options):
        reports = Report.objects.filter(negative=True)
        total_reports = reports.count()
        report_index = ReportIndex()

        done_reports_count = 0

        for report in reports:
            report_type = report.type
            template = report_type.django_template
            original_form_data = json.loads(report.original_form_data)
            t = Template(template)
            c = Context(original_form_data)
            report.rendered_original_form_data = t.render(c)
            # update with sql
            Report.objects.filter(id=report.id).update(rendered_original_form_data=report.rendered_original_form_data)
            # update elasticsearch
            report_index.update_object(report)

            done_reports_count += 1

            percent_progress = min((float(done_reports_count) / float(total_reports)) * 100, 100)
            sys.stdout.write('\r[%s] %s%% (%s/%d)' %
                             (('#' * int(percent_progress / 2)).ljust(50, ' '), int(percent_progress),
                              str(done_reports_count).rjust(10, ' '), total_reports))
            sys.stdout.flush()

