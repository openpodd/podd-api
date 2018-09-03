# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0100_recordspec'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='is_follow_action',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
