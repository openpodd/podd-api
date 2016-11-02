# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0047_user_is_anonymous'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdevice',
            name='apns_reg_id',
            field=models.CharField(default=b'', max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userdevice',
            name='android_id',
            field=models.CharField(max_length=100, blank=True),
            preserve_default=True,
        ),
    ]
