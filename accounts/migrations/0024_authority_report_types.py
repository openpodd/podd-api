# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0033_reporttype_authority'),
        ('accounts', '0023_authority'),
    ]

    operations = [
        migrations.AddField(
            model_name='authority',
            name='report_types',
            field=models.ManyToManyField(related_name='authority_report_types', null=True, to='reports.ReportType', blank=True),
            preserve_default=True,
        ),
    ]
