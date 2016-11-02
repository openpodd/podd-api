import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from py2neo import Graph

from accounts.models import Authority, Domain, User
from reports.models import AdministrationArea, ReportType


class Command(BaseCommand):
    args = '<domain_id domain_id ...>'
    help = 'Create node and relationship of User, Authority, AdministrationArea'

    def handle(self, *args, **options):

        graph = Graph(settings.NEO4J_CONNECTION_URL)

        if not args:
            args = Domain.objects.all().values_list('id', flat=True)
            # graph.cypher.execute("MATCH (n) DETACH DELETE n")
            graph.run("MATCH (n) DETACH DELETE n")

        for domain_id in args:
            print '> BUILDING INDEX FOR DOMAIN: %s' % domain_id
            try:
                domain = Domain.objects.get(pk=domain_id)
            except Domain.DoesNotExist:
                raise CommandError('Domain "%s" does not exist' % domain_id)

            graph.run("MATCH (n{domain_id:{d}}) DETACH DELETE n", d=domain_id)
            self.create_graph(domain.id)
            print "> END"


    def create_graph(self, domain_id):

        settings.CURRENT_DOMAIN_ID = domain_id
        Models = [User, Authority, AdministrationArea, ReportType]

        for Model in Models:
            print 'create_graph %s' % Model.__name__
            for inst in Model.objects.all():
                inst.update_graph_node()
                inst.update_graph_relations()
                sys.stdout.write('.')
                sys.stdout.flush()
            print ''


