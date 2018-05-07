# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0098_reportaccomplishment'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='map_to',
            field=models.ForeignKey(related_name='report_type_map_to', blank=True, to='reports.ReportType', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='parent_type',
            field=models.CharField(blank=True, max_length=255, null=True, choices=[(b'GENERAL', b'General'), (b'MERGE', b'Merge'), (b'DODD', b'DODD')]),
            preserve_default=True,
        ),
    ]
