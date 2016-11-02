# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0027_auto_20150622_1129'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='state',
            field=models.ForeignKey(related_name='report_state', blank=True, to='reports.ReportState', null=True),
            preserve_default=True,
        ),
    ]
