# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0025_auto_20150619_0704'),
    ]

    operations = [
        migrations.AddField(
            model_name='casedefinition',
            name='drop_if_exists',
            field=models.BooleanField(default=False, verbose_name='Rebuild Esper Schema ?'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='casedefinition',
            name='epl',
            field=models.TextField(help_text=b'sickCount.win:time(3 day) > 10', verbose_name='EPL Where Cause'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportstate',
            name='code',
            field=models.CharField(max_length=100),
            preserve_default=True,
        ),
    ]
