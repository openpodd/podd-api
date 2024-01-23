# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('animal', '0006_auto_20240118_0646'),
    ]

    operations = [
        migrations.AddField(
            model_name='animalrecord',
            name='birth_date',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
