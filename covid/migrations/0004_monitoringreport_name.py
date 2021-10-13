# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0003_auto_20211011_0836'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitoringreport',
            name='name',
            field=models.TextField(default=b'', max_length=255),
            preserve_default=True,
        ),
    ]
