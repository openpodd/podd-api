import logging

from django.utils.log import getLogger
from django.core.management import BaseCommand

from common.models import Domain
from accounts.models import Authority
from areas.models import Area
from reports.models import AdministrationArea


class Command(BaseCommand):
    help = 'Create public administration areas for specific domain'

    def handle(self, *args, **options):
        logger = getLogger('management_commands')

        assert len(args) > 0, "Please specify first argument as domain id"

        domain_id = int(args[0])
        try:
            domain = Domain.objects.get(id=domain_id)
            public_authority = Authority.objects.get(code="public_%d" % domain_id)

            for area in Area.objects.all():
                if area.location:
                    location = area.location
                elif area.longitude and area.latitude:
                    location = "POINT (%f %f)" % (area.longitude, area.latitude)
                else:
                    location = area.mpoly.centroid
                try:
                    administration_area = AdministrationArea.objects.get(area_code=area.code, domain_id=domain_id)
                    administration_area.name = area.name_th
                    administration_area.location = location
                    administration_area.mpoly = area.mpoly
                    administration_area.address = area.address
                    administration_area.save()
                    logger.info("Updated administration area .. %s (id:%d,area_code:%s)" % (area.name_th,
                                                                                            administration_area.id,
                                                                                            area.code))
                except AdministrationArea.DoesNotExist:
                    AdministrationArea.add_root(
                        domain=domain,
                        name=area.name_th,
                        location=location,
                        area_code=area.code,
                        mpoly=area.mpoly,
                        address=area.address,
                        code="public_%d_%s" % (domain_id, area.code),
                        authority=public_authority
                    )
                    logger.info("Created administration area .. %s" % area.name_th)

        except Domain.DoesNotExist:
            logger.error("Domain id=%d does not exist" % domain_id)
        except Authority.DoesNotExist:
            logger.error("Public authority for domain id=%d does not exist" % domain_id)

        return
