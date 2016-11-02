# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0007_auto_20141110_0356'),
    ]

    operations = [
        migrations.RenameField(
            model_name='report',
            old_name='user',
            new_name='created_by',
        ),
    ]
