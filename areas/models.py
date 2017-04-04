from django.contrib.gis.db import models
from common.models import DomainMixin


class Area(models.Model):
    code = models.CharField(max_length=100)
    province_id = models.IntegerField()
    # TODO: use below code instead when import done.
    level = models.IntegerField(default=0, null=True)
    parent = models.ForeignKey('Area', related_name="children", null=True)
    name_en = models.CharField(max_length=200)
    name_th = models.CharField(max_length=200)
    location = models.PointField(null=True)
    address = models.TextField()
    mpoly = models.MultiPolygonField(srid=4326)
    simplified_mpoly = models.MultiPolygonField(srid=4326, null=True)
    simplified_poly = models.PolygonField(srid=4326, null=True)
    simplified_type = models.CharField(max_length=50, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)


class PlaceCategory(DomainMixin):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)

    level0_key = models.CharField(max_length=255, null=True, blank=True, default='level0')
    level0_label = models.CharField(max_length=255, null=True, blank=True, default='Level0')
    level1_key = models.CharField(max_length=255, null=True, blank=True)
    level1_label = models.CharField(max_length=255, null=True, blank=True)
    level2_key = models.CharField(max_length=255, null=True, blank=True)
    level2_label = models.CharField(max_length=255, null=True, blank=True)

class Place(DomainMixin):

    category = models.ForeignKey(PlaceCategory)

    uuid = models.CharField(max_length=1024)
    level0_code = models.CharField(max_length=255)
    level0_name = models.CharField(max_length=1024)
    level1_code = models.CharField(max_length=255, null=True, blank=True)
    level1_name = models.CharField(max_length=1024, null=True, blank=True)
    level2_code = models.CharField(max_length=255, null=True, blank=True)
    level2_name = models.CharField(max_length=1024, null=True, blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return '%s %s %s' % (self.level0_name, self.level1_name, self.level2_name)

    def save(self, *args, **kwargs):

        self.uuid = '%s%s%s%s' % (self.category.code, self.level0_code, (self.level1_code or ''), (self.level2_code or ''))

        try:
            if not self.id:
                exist_place = Place.objects.get(uuid=self.uuid)
                exist_place.category = self.category
                exist_place.level0_code = self.level0_code
                exist_place.level0_name = self.level0_name
                exist_place.level1_code = self.level1_code
                exist_place.level1_name = self.level1_name
                exist_place.level2_code = self.level2_code
                exist_place.level2_name = self.level2_name
                exist_place.latitude    = self.latitude
                exist_place.longitude   = self.longitude

                exist_place.save()

        except Place.DoesNotExist:
            super(Place, self).save(*args, **kwargs)
            return True
