# -*- encoding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Authority
from common.functions import get_data_from_csv
from reports.models import AdministrationArea


class Command(BaseCommand):
    args = 'file_path.csv domain_id'
    help = 'Import Authority with code from csv: file_path.csv'

    def handle(self, *args, **options):

        if not args:
            raise CommandError('Please input csv path')

        domain_id = args[0]
        settings.CURRENT_DOMAIN_ID = domain_id

        # first pass
        print("========= first pass ==========")
        for authority in Authority.objects.filter(domain_id=domain_id):
            authority.save()

        for area in AdministrationArea.objects.filter(domain_id=domain_id):
            area.save()
