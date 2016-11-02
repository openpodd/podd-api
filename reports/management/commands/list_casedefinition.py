import datetime
from django.conf import settings
from django.core.management import BaseCommand
from reports.models import CaseDefinition


class Command(BaseCommand):
    args = 'domain in TODO'
    help = 'Export casedefinition'

    def handle(self, *args, **options):

        print args

        settings.CURRENT_DOMAIN_ID = int(args[0]) if args else 1

        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\r' % ('Date', 'Report Type', 'Description', 'Condition', 'From State', 'To State', 'ID')
        for case in CaseDefinition.objects.all():
            print '%s\t%s\t%s\t%s\t%s\t%s\t%s\r' % (
                datetime.date.today(),
                case.report_type.name,
                case.description,
                case.epl.replace('\r', ' ').replace('\n', ' '),
                case.from_state.name,
                case.to_state.name,
                case.id
            )