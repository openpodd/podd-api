# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0051_auto_20151012_0706'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdevice',
            name='android_id',
            field=models.CharField(default=b'', max_length=100, blank=True),
            preserve_default=True,
        ),
    ]
