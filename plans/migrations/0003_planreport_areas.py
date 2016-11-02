# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0072_administrationarea_qgis_id'),
        ('plans', '0002_auto_20151221_1143'),
    ]

    operations = [
        migrations.AddField(
            model_name='planreport',
            name='areas',
            field=models.ManyToManyField(to='reports.AdministrationArea', null=True, blank=True),
            preserve_default=True,
        ),
    ]
