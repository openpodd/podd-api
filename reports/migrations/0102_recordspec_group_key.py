# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0101_reporttype_is_follow_action'),
    ]

    operations = [
        migrations.AddField(
            model_name='recordspec',
            name='group_key',
            field=models.IntegerField(default=0, choices=[(0, b'user'), (1, b'all'), (2, b'authority')]),
            preserve_default=True,
        ),
    ]
