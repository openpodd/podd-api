# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0096_auto_20170920_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reporttype',
            name='notification_buffer',
            field=models.FloatField(help_text=b'Radius of buffer that use to find intersects authorities', null=True, blank=True),
            preserve_default=True,
        ),
    ]
