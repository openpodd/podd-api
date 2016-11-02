# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0010_administrationarea_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='template',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
    ]
