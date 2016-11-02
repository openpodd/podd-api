# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0026_authority_spreadsheet_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authority',
            name='spreadsheet_url',
        ),
        migrations.AddField(
            model_name='authority',
            name='spreadsheet_key',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
