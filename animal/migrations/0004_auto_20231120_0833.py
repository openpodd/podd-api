# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('animal', '0003_remove_animalrecord_addr_district'),
    ]

    operations = [
        migrations.AlterField(
            model_name='animalrecord',
            name='addr_moo',
            field=models.CharField(max_length=10, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='animalrecord',
            name='addr_road',
            field=models.CharField(max_length=100, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='animalrecord',
            name='addr_soi',
            field=models.CharField(max_length=100, blank=True),
            preserve_default=True,
        ),
    ]
