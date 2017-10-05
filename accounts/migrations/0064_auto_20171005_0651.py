# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0063_authority_mpoly'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authority',
            name='area',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
            preserve_default=True,
        ),
    ]
