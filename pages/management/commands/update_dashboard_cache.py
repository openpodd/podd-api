# -*- encoding: utf-8 -*-

import json

from django.core.management import BaseCommand
from django.template import Template, Context
from reports.models import Report, ReportType


class Command(BaseCommand):

    help = 'Update public report data'

    def handle(self, *args, **options):

        from pages.tasks import fetch_dashboard_for_every_days
        fetch_dashboard_for_every_days()