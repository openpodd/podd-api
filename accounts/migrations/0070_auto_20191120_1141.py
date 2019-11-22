# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0069_userdevice_fcm_reg_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdevice',
            name='fcm_reg_id',
            field=models.CharField(max_length=255, null=True),
            preserve_default=True,
        ),
    ]
