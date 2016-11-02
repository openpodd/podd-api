# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0055_auto_20160125_0705'),
        ('reports', '0079_googlecalendarresponse'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='spreadsheetresponse',
            name='administration_areas',
        ),
        migrations.AddField(
            model_name='spreadsheetresponse',
            name='authorities',
            field=models.ManyToManyField(related_name='authority_response', null=True, to='accounts.Authority', blank=True),
            preserve_default=True,
        ),
    ]
