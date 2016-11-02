# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_auto_20150625_1027'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='anonymous_send',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
