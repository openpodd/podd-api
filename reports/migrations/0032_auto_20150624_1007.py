# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0031_auto_20150623_0318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casedefinition',
            name='from_state',
            field=models.ForeignKey(related_name='from_state', blank=True, to='reports.ReportState', help_text=b'If none, default state is report', null=True),
            preserve_default=True,
        ),
    ]
