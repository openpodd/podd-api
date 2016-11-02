# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_auto_20150119_0703'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupadministrationarea',
            name='role',
            field=models.PositiveIntegerField(default=1, choices=[(1, b'Reporter'), (2, b'Prospector')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupreporttype',
            name='role',
            field=models.PositiveIntegerField(default=1, choices=[(1, b'Reporter'), (2, b'Prospector')]),
            preserve_default=True,
        ),
    ]
