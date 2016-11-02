# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0011_auto_20150902_0816'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationtemplate',
            name='data',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
