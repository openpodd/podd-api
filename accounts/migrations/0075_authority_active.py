# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0074_auto_20220307_0403'),
    ]

    operations = [
        migrations.AddField(
            model_name='authority',
            name='active',
            field=models.NullBooleanField(),
            preserve_default=True,
        ),
    ]
