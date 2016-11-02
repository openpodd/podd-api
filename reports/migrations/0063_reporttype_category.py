# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0062_auto_20151020_0651'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='category',
            field=models.ForeignKey(related_name='report_type_category', blank=True, to='reports.ReportTypeCategory', null=True),
            preserve_default=True,
        ),
    ]
