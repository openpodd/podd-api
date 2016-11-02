# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flags', '0005_data_flags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flag',
            name='priority',
            field=models.PositiveIntegerField(default=0, choices=[(0, b'None'), (1, b'Ignore'), (2, b'OK'), (3, b'Contact'), (4, b'Follow'), (5, b'Case')]),
            preserve_default=True,
        ),
    ]
