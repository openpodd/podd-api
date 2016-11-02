# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0048_auto_20151008_1014'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_public',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
