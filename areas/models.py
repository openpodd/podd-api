from django.contrib.gis.db import models


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
