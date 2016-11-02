# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0016_reportimage_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='django_template',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
    ]
