# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0047_report_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='summary_template',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
    ]
