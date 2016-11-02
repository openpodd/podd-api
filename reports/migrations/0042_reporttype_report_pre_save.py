# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0041_migrate_data_report_type_default_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='report_pre_save',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
