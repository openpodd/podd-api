# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0013_auto_20141124_0823'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reporttype',
            options={'ordering': ['name']},
        ),
    ]
