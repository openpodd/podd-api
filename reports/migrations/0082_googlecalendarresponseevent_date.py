# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0081_googlecalendarresponseevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='googlecalendarresponseevent',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2016, 2, 10, 9, 52, 34, 793004, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
