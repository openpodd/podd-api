# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0019_reporttype_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reporttype',
            name='code',
            field=models.CharField(unique=True, max_length=100),
            preserve_default=True,
        ),
    ]
