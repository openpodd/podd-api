# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_auto_20141110_0926'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportcomment',
            name='file_url',
            field=models.URLField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
