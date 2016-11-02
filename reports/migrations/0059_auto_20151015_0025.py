# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0058_administrationarea_area_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='administrationarea',
            name='area_code',
            field=models.CharField(max_length=10, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='administrationarea',
            name='mpoly',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
            preserve_default=True,
        ),
    ]
