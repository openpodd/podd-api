# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0050_auto_20150917_0930'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportstateunique',
            name='state',
            field=models.ForeignKey(related_name='report_state_unique_state', blank=True, to='reports.ReportState', null=True),
            preserve_default=True,
        ),
    ]
