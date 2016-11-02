# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0014_auto_20141203_0354'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='code',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
    ]
