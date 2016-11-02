# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0061_auto_20151016_0958'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='administration_area',
            field=models.ForeignKey(related_name='reports', blank=True, to='reports.AdministrationArea', null=True),
            preserve_default=True,
        ),
    ]
