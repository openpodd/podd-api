# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0094_auto_20170517_1024'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='report_post_save',
            field=models.TextField(help_text=b'Variables are: report, json, geos, geos_util', null=True, blank=True),
            preserve_default=True,
        ),
    ]
