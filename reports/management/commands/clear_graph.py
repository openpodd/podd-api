from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import sys
from py2neo import Graph

from accounts.models import Authority, Domain, User
from reports.models import AdministrationArea, ReportType


class Command(BaseCommand):
    args = '<domain_id domain_id ...>'
    help = 'Clear node and relationship of User, Authority, AdministrationArea'

    def handle(self, *args, **options):

        graph = Graph(settings.NEO4J_CONNECTION_URL)
        graph.delete_all()



