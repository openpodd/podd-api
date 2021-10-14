# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0005_authorityinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitoringreport',
            name='followup_count',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='monitoringreport',
            name='latest_followup_date',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
