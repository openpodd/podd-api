# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0067_auto_20151026_0909'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='weight',
            field=models.FloatField(default=0, null=True, blank=True),
            preserve_default=True,
        ),
    ]
