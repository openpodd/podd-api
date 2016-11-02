from django.utils.log import getLogger
from django.core.management import BaseCommand
from feed.functions import warm_cache_public_feed


class Command(BaseCommand):
    help = 'Warm feed cache for all public domains'

    def handle(self, *args, **options):
        logger = getLogger('management_commands')
        warm_cache_public_feed(logger)
