# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0102_recordspec_group_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportimage',
            name='image_url',
            field=models.URLField(max_length=800),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportimage',
            name='thumbnail_url',
            field=models.URLField(max_length=800),
            preserve_default=True,
        ),
    ]
