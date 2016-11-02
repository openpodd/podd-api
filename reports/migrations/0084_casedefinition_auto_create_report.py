# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0083_auto_20160506_1238'),
    ]

    operations = [
        migrations.AddField(
            model_name='casedefinition',
            name='auto_create_report',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
