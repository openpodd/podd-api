# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0068_user_lineid'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdevice',
            name='fcm_reg_id',
            field=models.CharField(max_length=100, null=True),
            preserve_default=True,
        ),
    ]
