# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0071_auto_20151216_0821'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='qgis_id',
            field=models.CharField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
    ]
