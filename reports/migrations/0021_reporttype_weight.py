# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0020_auto_20150226_0832'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='weight',
            field=models.FloatField(null=True),
            preserve_default=True,
        ),
    ]
