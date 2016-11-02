# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0037_auto_20150826_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='original_form_data',
            field=models.TextField(default='', blank=True),
            preserve_default=False,
        ),
    ]
