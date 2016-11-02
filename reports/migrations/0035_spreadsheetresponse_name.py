# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0034_spreadsheetresponse'),
    ]

    operations = [
        migrations.AddField(
            model_name='spreadsheetresponse',
            name='name',
            field=models.CharField(default=datetime.datetime(2015, 7, 20, 2, 52, 32, 952333, tzinfo=utc), max_length=255),
            preserve_default=False,
        ),
    ]
