# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0103_auto_20190224_1000'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='merge_with_parent',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
