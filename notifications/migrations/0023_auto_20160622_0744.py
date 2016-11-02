# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0022_auto_20160506_1238'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationtemplate',
            name='delayed_time',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notificationtemplate',
            name='type',
            field=models.IntegerField(default=1, max_length=2, choices=[(1, b'Report'), (2, b'Reporter Feedback'), (3, b'Notify Follow Up'), (4, b'Late Follow Up'), (5, b'Private'), (6, b'Delayed Follow Up')]),
            preserve_default=True,
        ),
    ]
