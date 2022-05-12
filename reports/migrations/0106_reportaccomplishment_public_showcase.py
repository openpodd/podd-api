# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0105_auto_20220307_0342'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportaccomplishment',
            name='public_showcase',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
