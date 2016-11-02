# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0009_reportcomment_file_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='address',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
    ]
