# -*- encoding: utf-8 -*-

from optparse import make_option

import copy
from django.core.management.base import BaseCommand

from accounts.models import Authority
from common.models import Domain
from reports.models import ReportType, ReportState, ReportTypeCategory, CaseDefinition


class Command(BaseCommand):
    args = '<from_domain> <to_domain> <report_type_id report_type_id ...>'
    help = 'Copy report types'
    option_list = BaseCommand.option_list + (
        make_option(
            '--from-authority',
            action='store',
            dest='from_authority',
            default=None,
            help='Specify origin authority'
        ),
        make_option(
            '--to-authority',
            action='store',
            dest='to_authority',
            default=None,
            help='Specify target authority'
        ),
        make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Whether to force mode, default is dry_run mode'
        )
    )

    def _copy_report_states(self, from_domain, to_domain, from_report_type, to_report_type, dry_run=True):
        original_report_states = ReportState.objects.filter(domain=from_domain, report_type=from_report_type)

        for original_report_state in original_report_states:
            should_save_report_state = False
            try:
                report_state = ReportState.objects.get(domain=to_domain, report_type=to_report_type, code=original_report_state.code)
                if report_state.name != original_report_state.name:
                    report_state.name = original_report_state.name
                    should_save_report_state = True
            except ReportState.DoesNotExist:
                should_save_report_state = True
                report_state = copy.deepcopy(original_report_state)

                report_state.pk = None
                report_state.domain = to_domain
                report_state.report_type = to_report_type

            if should_save_report_state:
                print "Will copy report state from %s to %s using this data:" % (from_domain.name, to_domain.name)
                print " [FROM] id:%s domain:%s authority:%s report_type:%s report_state_code:%s" % (
                    original_report_state.pk, original_report_state.domain.name, original_report_state.report_type.authority, original_report_state.report_type, original_report_state.code)
                print "   [TO] id:%s domain:%s authority:%s report_type:%s report_state_code:%s" % (
                    report_state.pk, report_state.domain.name, report_state.report_type.authority, report_state.report_type, report_state.code)

                if not dry_run:
                    report_state.save()
                    print "  - Saved id: %s" % report_state.pk

            print ""

    def _copy_case_definitions(self, from_domain, to_domain, from_report_type, to_report_type, dry_run=True):
        original_case_definitions = CaseDefinition.objects.filter(domain=from_domain, report_type=from_report_type)

        for original_case_definition in original_case_definitions:
            should_save_case_definition = False
            try:
                case_definition = CaseDefinition.objects.get(domain=to_domain, report_type=to_report_type, code=original_case_definition.code)
                if case_definition.epl != original_case_definition.epl:
                    case_definition.epl = original_case_definition.epl
                    should_save_case_definition = True
                if case_definition.description != original_case_definition.description:
                    case_definition.description = original_case_definition.description
                    should_save_case_definition = True
                if case_definition.accumulate != original_case_definition.accumulate:
                    case_definition.accumulate = original_case_definition.accumulate
                    should_save_case_definition = True
                if case_definition.window != original_case_definition.window:
                    case_definition.window = original_case_definition.window
                    should_save_case_definition = True
            except CaseDefinition.DoesNotExist:
                should_save_case_definition = True
                case_definition = copy.deepcopy(original_case_definition)

                case_definition.pk = None
                case_definition.domain = to_domain
                case_definition.report_type = to_report_type

            if should_save_case_definition:
                print "Will copy case definition from %s to %s using this data:" % (from_domain.name, to_domain.name)
                print " [FROM] id:%s domain:%s report_type:%s case_def_code:%s" % (
                    original_case_definition.pk, original_case_definition.domain, original_case_definition.report_type.name, original_case_definition.code)
                print "   [TO] id:%s domain:%s report_type:%s case_def_code:%s" % (
                    case_definition.pk, case_definition.domain.name, case_definition.report_type.name, original_case_definition.code)

                if not dry_run:
                    case_definition.from_state = ReportState.objects.get(domain=to_domain, report_type=to_report_type, code=original_case_definition.from_state.code)
                    case_definition.to_state = ReportState.objects.get(domain=to_domain, report_type=to_report_type, code=original_case_definition.to_state.code)
                    case_definition.save()
                    print "  - Saved id: %s" % case_definition.pk

            print "--"

    def _copy_report_type_categories(self, from_domain, to_domain, dry_run=True, report_type_ids=[]):
        original_report_type_categories = ReportTypeCategory.objects.filter(domain=from_domain, report_type_category__id__in=report_type_ids)

        for original_report_type_category in original_report_type_categories:
            try:
                report_type_category = ReportTypeCategory.objects.get(domain=to_domain, code=original_report_type_category.code)
                if report_type_category.name != original_report_type_category.name:
                    report_type_category.name = original_report_type_category.name
                    print "Will update report type category from %s to %s using this data:" % (
                    from_domain.name, to_domain.name)
                    print " [FROM] id:%s domain:%s code:%s" % (
                        original_report_type_category.pk, original_report_type_category.domain,
                        original_report_type_category.code)
                    print "   [TO] id:%s domain:%s code:%s" % (
                        report_type_category.pk, report_type_category.domain.name, report_type_category.code)
                    if not dry_run:
                        report_type_category.save()
                        print "  - Saved id: %s" % report_type_category.pk
            except ReportTypeCategory.DoesNotExist:
                report_type_category = copy.deepcopy(original_report_type_category)

                report_type_category.pk = None
                report_type_category.domain = to_domain

                print "Will copy report type category from %s to %s using this data:" % (from_domain.name, to_domain.name)
                print " [FROM] id:%s domain:%s code:%s" % (
                    original_report_type_category.pk, original_report_type_category.domain, original_report_type_category.code)
                print "   [TO] id:%s domain:%s code:%s" % (
                    report_type_category.pk, report_type_category.domain.name, report_type_category.code)

                if not dry_run:
                    report_type_category.save()
                    print "  - Saved id: %s" % report_type_category.pk

                print "--"

    def _copy_report_types(self, from_domain, to_domain, from_authority=None, to_authority=None, report_type_ids=[],
                          dry_run=True):
        if dry_run:
            print ">> DRY RUN <<\n"

        self._copy_report_type_categories(from_domain, to_domain, dry_run, report_type_ids)

        original_report_types = ReportType.objects.filter(domain=from_domain)
        if from_authority:
            original_report_types = original_report_types.filter(authority=from_authority)

        if report_type_ids:
            original_report_types = original_report_types.filter(id__in=report_type_ids)

        for original_report_type in original_report_types:
            should_save_report_type = False

            try:
                report_type = ReportType.objects.get(domain=to_domain, code=original_report_type.code)
                if report_type.form_definition != original_report_type.form_definition:
                    report_type.form_definition = original_report_type.form_definition
                    should_save_report_type = True
                if report_type.name != original_report_type.name:
                    report_type.name = original_report_type.name
                    should_save_report_type = True
                if report_type.template != original_report_type.template:
                    report_type.template = original_report_type.template
                    should_save_report_type = True
                if report_type.django_template != original_report_type.django_template:
                    report_type.django_template = original_report_type.django_template
                    should_save_report_type = True
                if report_type.summary_template != original_report_type.summary_template:
                    report_type.summary_template = original_report_type.summary_template
                    should_save_report_type = True

            except ReportType.DoesNotExist:
                should_save_report_type = True
                report_type = copy.deepcopy(original_report_type)

                report_type.pk = None
                report_type.domain = to_domain
                report_type.default_state = None
                if not dry_run and original_report_type.category:
                    report_type.category = ReportTypeCategory.objects.get(domain=to_domain, code=original_report_type.category.code)

                if to_authority:
                    report_type.authority = to_authority
                else:
                    report_type.authority = None

            if should_save_report_type:
                print "Will copy report type from %s to %s using this data:" % (from_domain.name, to_domain.name)
                print " [FROM] id:%s domain:%s authority:%s report_type:%s" % (original_report_type.pk, original_report_type.domain.name, original_report_type.authority, original_report_type.name)
                print "   [TO] id:%s domain:%s authority:%s report_type:%s" % (report_type.pk, report_type.domain.name, report_type.authority, report_type.name)
                if not dry_run:
                    report_type.save(set_default_state=True)
                    print "  - Saved id: %s" % report_type.pk
                print ""
c
            # copy report states
            self._copy_report_states(from_domain, to_domain, from_report_type=original_report_type,
                                     to_report_type=report_type, dry_run=dry_run)

            # copy case definitions
            self._copy_case_definitions(from_domain, to_domain, from_report_type=original_report_type,
                                     to_report_type=report_type, dry_run=dry_run)

            if should_save_report_type:
                try:
                    default_state = ReportState.objects.get(report_type=report_type, code='report')
                    if not report_type.default_state or default_state.id != report_type.default_state.id:
                        print ">> Then will set default state to %s" % default_state.name
                        if not dry_run:
                            report_type.default_state = default_state
                            report_type.save()
                except ReportState.DoesNotExist:
                    pass

            print "---------------------"

    def handle(self, *args, **options):
        from_domain = Domain.objects.get(id=args[0])
        to_domain = Domain.objects.get(id=args[1])
        report_type_ids = list(args[2:])

        from_authority = options['from_authority']
        if from_authority:
            from_authority = Authority.objects.get(domain=from_domain, id=from_authority)

        to_authority = options['to_authority']
        if to_authority:
            to_authority = Authority.objects.get(domain=to_domain, id=to_authority)

        dry_run = not options['force']

        self._copy_report_types(from_domain, to_domain, from_authority, to_authority, report_type_ids, dry_run)
