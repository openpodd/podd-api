# -*- encoding: utf-8 -*-

from optparse import make_option

import json
from django.core.management import BaseCommand

from common.models import Domain
from reports.models import ReportType, ReportState


class Command(BaseCommand):
    args = '<domain> <filename>'
    help = '''update report state from specification file
file example.
{
	report: 'reportName',
	states: [
		['report', 'Report'],
	    ['case', 'Case'],
		['false-report', 'False Report'],
		['complete-case', 'Complete Case'],
		['finish', 'Finish']
	],
	renameStates: {
		'insignificant-report': ['inconclusive-report', 'Inconclusive Report']
	}
}    
    '''
    option_list = BaseCommand.option_list + (
        make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Whether to force mode, default is dry_run mode'
        ),
    )

    def handle(self, *args, **options):
        if len(args) != 2:
            print 'usage: ./manage.py update_report_state domain_id filename'
            exit(0)

        dry_run = not options['force']

        domain = Domain.objects.get(id=args[0])
        filename = args[1]
        with open(filename, 'r') as f:
            spec = json.load(f)
            reportType = ReportType.objects.filter(domain=domain, name=spec['report'])[0]

            for (code, name) in spec['states']:
                n = ReportState.objects.filter(code=code, name=name, report_type=reportType).count()
                if n == 0:
                    if dry_run:
                        print "create reportState(code=%s, name=%s)" % (code, name)
                    else:
                        new_state = ReportState()
                        new_state.domain = domain
                        new_state.code = code
                        new_state.name = name
                        new_state.report_type = reportType
                        new_state.save()
            if 'reportStates' in spec:
                for code, (new_code, new_name) in spec['renameStates'].iteritems():
                    n = ReportState.objects.filter(code=code, report_type=reportType).count()
                    if n == 1:
                        state = ReportState.objects.get(code=code, report_type=reportType)
                        if dry_run:
                            print "rename report state id=%d from %s to %s" % (state.id, state.code, new_code)
                        else:
                            state.code = new_code
                            state.name = new_name
                            state.save()
            if 'removeStates' in spec:
                for code in spec['removeStates']:
                    n = ReportState.objects.filter(code=code, report_type=reportType).count()
                    if n == 1:
                        state = ReportState.objects.get(code=code, report_type=reportType)
                        if dry_run:
                            print "delete report state id=%d, name=%s" % (state.id, state.name)
                        else:
                            state.delete()






