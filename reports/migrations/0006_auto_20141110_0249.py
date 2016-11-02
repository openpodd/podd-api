# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_auto_20141107_0509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='guid',
            field=models.TextField(unique=True),
            preserve_default=True,
        ),
    ]
