# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0020_notification_is_seen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationtemplate',
            name='type',
            field=models.IntegerField(default=1, max_length=2, choices=[(1, b'Report'), (2, b'Reporter Feedback'), (3, b'Notify Follow Up'), (4, b'Late Follow Up'), (5, b'Private')]),
            preserve_default=True,
        ),
    ]
