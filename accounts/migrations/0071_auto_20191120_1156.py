# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0070_auto_20191120_1141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdevice',
            name='fcm_reg_id',
            field=models.CharField(max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
