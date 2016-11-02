# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_auto_20141107_0458'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportimage',
            name='guid',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='reportimage',
            name='note',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
    ]
