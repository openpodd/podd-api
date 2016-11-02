# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0055_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='is_public',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
