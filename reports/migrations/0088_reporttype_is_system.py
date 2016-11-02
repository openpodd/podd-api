# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0087_reportstate_allow_to_states'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='is_system',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
