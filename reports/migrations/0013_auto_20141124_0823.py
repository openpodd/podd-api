# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0012_auto_20141114_0820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportcomment',
            name='file_url',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
