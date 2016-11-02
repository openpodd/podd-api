from django.utils.log import getLogger
from django.core.management import BaseCommand
from accounts.models import Authority
from common.models import Domain


class Command(BaseCommand):
    help = 'Create public authority for all existing domains'

    def handle(self, *args, **options):
        logger = getLogger('management_commands')

        domains = Domain.objects.all()
        for domain in domains:
            try:
                Authority.objects.get(name="public_%d" % domain.id)
            except Authority.DoesNotExist:
                Authority.objects.create(
                    code='public_%s' % domain.id,
                    name='public_%s' % domain.id,
                    description='public',
                    domain_id=domain.id
                )
                logger.info("Created public authority for domain %s" % domain.name)

        return
