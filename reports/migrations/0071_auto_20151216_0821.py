# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0070_auto_20151123_0351'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='contacts',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='administrationarea',
            name='remark',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
