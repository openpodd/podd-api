# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('animal', '0004_auto_20231120_0833'),
    ]

    operations = [
        migrations.AlterField(
            model_name='animalrecord',
            name='addr_moo',
            field=models.CharField(max_length=100, blank=True),
            preserve_default=True,
        ),
    ]
