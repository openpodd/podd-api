# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0092_auto_20170404_0517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reporttype',
            name='report_pre_save',
            field=models.TextField(help_text=b'Variables are: report, json, geos, geos_util', null=True, blank=True),
            preserve_default=True,
        ),
    ]
