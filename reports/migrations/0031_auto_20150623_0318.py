# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0030_data_report_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casedefinition',
            name='from_state',
            field=models.ForeignKey(related_name='from_state', blank=True, to='reports.ReportState', null=True),
            preserve_default=True,
        ),
    ]
