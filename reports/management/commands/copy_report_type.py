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
            try:
                report_state = ReportState.objects.get(domain=to_domain, report_type=to_report_type, code=original_report_state.code)
            except ReportState.DoesNotExist:
                report_state = copy.deepcopy(original_report_state)

                report_state.pk = None
                report_state.domain = to_domain
                report_state.report_type = to_report_type

            print "Will copy report state from %s to %s using this data:" % (from_domain.name, to_domain.name)
            print " [FROM] id:%s domain:%s authority:%s report_type:%s" % (
                original_report_state.pk, original_report_state.domain, original_report_state.report_type.authority, original_report_state.report_type)
            print "   [TO] id:%s domain:%s authority:%s report_type:%s" % (
                report_state.pk, report_state.domain, report_state.report_type.authority, report_state.report_type)

            if not dry_run:
                report_state.save()
                print "  - Saved id: %s" % report_state.pk

            print ""

    def _copy_case_definitions(self, from_domain, to_domain, from_report_type, to_report_type, dry_run=True):
        original_case_definitions = CaseDefinition.objects.filter(domain=from_domain, report_type=from_report_type)

        for original_case_definition in original_case_definitions:

            try:
                case_definition = CaseDefinition.objects.get(domain=to_domain, report_type=to_report_type, code=original_case_definition.code)
            except CaseDefinition.DoesNotExist:
                case_definition = copy.deepcopy(original_case_definition)

                case_definition.pk = None
                case_definition.domain = to_domain
                case_definition.report_type = to_report_type

            case_definition.from_state = ReportState.objects.get(domain=to_domain, report_type=to_report_type, code=original_case_definition.from_state.code)
            case_definition.to_state = ReportState.objects.get(domain=to_domain, report_type=to_report_type, code=original_case_definition.to_state.code)

            print "Will copy case definition from %s to %s using this data:" % (from_domain.name, to_domain.name)
            print " [FROM] id:%s domain:%s report_type:%s" % (
                original_case_definition.pk, original_case_definition.domain, original_case_definition.report_type)
            print "   [TO] id:%s domain:%s report_type:%s" % (
                case_definition.pk, case_definition.domain, case_definition.report_type)

            if not dry_run:
                case_definition.save()
                print "  - Saved id: %s" % case_definition.pk

            print "--"

    def _copy_report_type_categories(self, from_domain, to_domain, dry_run=True):
        original_report_type_categories = ReportTypeCategory.objects.filter(domain=from_domain)

        for original_report_type_category in original_report_type_categories:
            try:
                report_type_category = ReportTypeCategory.objects.get(domain=to_domain, code=original_report_type_category.code)
            except ReportTypeCategory.DoesNotExist:
                report_type_category = copy.deepcopy(original_report_type_category)

                report_type_category.pk = None
                report_type_category.domain = to_domain

                print "Will copy report type category from %s to %s using this data:" % (from_domain.name, to_domain.name)
                print " [FROM] id:%s domain:%s code:%s" % (
                    original_report_type_category.pk, original_report_type_category.domain, original_report_type_category.code)
                print "   [TO] id:%s domain:%s code:%s" % (
                    report_type_category.pk, report_type_category.domain, report_type_category.code)

                if not dry_run:
                    report_type_category.save()
                    print "  - Saved id: %s" % report_type_category.pk

                print "--"

    def _copy_report_types(self, from_domain, to_domain, from_authority=None, to_authority=None, report_type_ids=[],
                          dry_run=True):
        if dry_run:
            print ">> DRY RUN <<\n"

        self._copy_report_type_categories(from_domain, to_domain, dry_run)

        original_report_types = ReportType.objects.filter(domain=from_domain)
        if from_authority:
            original_report_types = original_report_types.filter(authority=from_authority)

        if report_type_ids:
            original_report_types = original_report_types.filter(id__in=report_type_ids)

        for original_report_type in original_report_types:
            try:
                report_type = ReportType.objects.get(domain=to_domain, code=original_report_type.code)
            except ReportType.DoesNotExist:
                report_type = copy.deepcopy(original_report_type)

                report_type.pk = None
                report_type.domain = to_domain
                report_type.default_state = None
                if not dry_run:
                    report_type.category = ReportTypeCategory.objects.get(domain=to_domain, code=original_report_type.category.code)

                if to_authority:
                    report_type.authority = to_authority
                else:
                    report_type.authority = None

            print "Will copy report type from %s to %s using this data:" % (from_domain.name, to_domain.name)
            print " [FROM] id:%s domain:%s authority:%s" % (original_report_type.pk, original_report_type.domain, original_report_type.authority)
            print "   [TO] id:%s domain:%s authority:%s" % (report_type.pk, report_type.domain, report_type.authority)
            if not dry_run:
                report_type.save(set_default_state=True)
                print "  - Saved id: %s" % report_type.pk
            print ""

            # copy report states
            self._copy_report_states(from_domain, to_domain, from_report_type=original_report_type,
                                     to_report_type=report_type, dry_run=dry_run)

            # copy case definitions
            self._copy_case_definitions(from_domain, to_domain, from_report_type=original_report_type,
                                     to_report_type=report_type, dry_run=dry_run)

            if not dry_run:
                default_state = ReportState.objects.get(report_type=report_type, code='report')
                print ">> Then will set default state to %s" % default_state.name
                report_type.default_state = default_state
                report_type.save()

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