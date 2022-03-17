from django.conf import settings
from django.core.management import BaseCommand, CommandError

from accounts.models import Authority
from common.functions import get_data_from_csv
from reports.models import AdministrationArea


class Command(BaseCommand):
    args = 'authority_list.csv'
    help = "create missing administration_area"

    def handle(self, *args, **options):
        areas =  []
        authorities = []

        if not args:
            raise CommandError("Please input csv file")

        file_path = args[0]
        data = get_data_from_csv(file_path)

        for row in data:
            domain_id = row['domain_id']
            settings.CURRENT_DOMAIN_ID = domain_id
            try:
                authority = Authority.objects.get(pk=row['id'])

                lat = row['lat']
                lng = row['lng']
                point = 'POINT (100.31 14.35)'
                if lat and lng:
                    point = 'POINT (%s %s)' % (lng, lat)

                if not AdministrationArea.objects.filter(authority_id=authority.id).exists():
                    area = AdministrationArea.objects.create(
                        name=row['name'],
                        address=row['name'],
                        location=point,
                        code=row['code'],
                        authority=authority,
                        domain_id=domain_id
                    )
                    print("Create Area from %s" % (row['name'],))
                else:
                    print("Area for %s is already exists." % (row['name'],))

            except Authority.DoesNotExist:
                print("Authority %s not found." % (row['name'],))

