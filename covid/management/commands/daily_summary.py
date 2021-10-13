from django.core.management.base import BaseCommand
from covid.tasks import daily_summarize


class Command(BaseCommand):
    help = "create yesterday covid monitoring summarize"

    def handle(self, *args, **options):
        daily_summarize()
