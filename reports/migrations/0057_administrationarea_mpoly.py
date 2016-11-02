# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0056_report_is_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='mpoly',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True),
            preserve_default=True,
        ),
    ]
