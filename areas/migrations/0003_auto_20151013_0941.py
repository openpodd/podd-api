# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('areas', '0002_auto_20151013_0939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='area',
            name='simplified_mpoly',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='area',
            name='simplified_poly',
            field=django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='area',
            name='simplified_type',
            field=models.CharField(max_length=50, null=True),
            preserve_default=True,
        ),
    ]
