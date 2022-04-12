# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0008_auto_20211111_0635'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='is_test',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
