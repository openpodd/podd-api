# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='area',
            field=models.ForeignKey(blank=True, to='reports.AdministrationArea', null=True),
            preserve_default=True,
        ),
    ]
