from django.apps import AppConfig
from django.conf import settings
from django.db import ProgrammingError
from django.db.models.signals import pre_migrate, post_migrate
from py2neo import Graph
from py2neo.packages.httpstream import SocketError
from common.models import Domain


def common_callback(sender, **kwargs):
    defaults = settings.DEFAULT_DOMAIN.copy()

    current_domain_id = 1
    try:
        current_domain_id = settings.CURRENT_DOMAIN_ID
    except AttributeError:
        pass

    if current_domain_id == 0 and settings.TESTING:
        graph = Graph(settings.NEO4J_CONNECTION_URL)
        try:
            graph.run("MATCH({domain_id: 0}) - [r] - ({domain_id: %s}) DETACH DELETE r" % current_domain_id)
        except SocketError:
            raise Exception('Please, start neo4j server')

    defaults['id'] = current_domain_id
    try:
        domain, created = Domain.objects.get_or_create(id=current_domain_id, defaults=defaults)
        if created:
            print '!! Create default domain: %s(%s) [%d]' % (domain.name, domain.code, domain.id)

    except ProgrammingError:
        print '!! Can not create default domain, try again later with next migrate'


class CommonAppConfig(AppConfig):

    name = 'common'
    verbose_name = 'Common'

    def ready(self):
        pre_migrate.connect(common_callback, sender=self)
        post_migrate.connect(common_callback, sender=self)
