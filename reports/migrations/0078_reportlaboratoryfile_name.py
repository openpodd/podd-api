# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0077_auto_20160203_0733'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportlaboratoryfile',
            name='name',
            field=models.TextField(default=datetime.datetime(2016, 2, 3, 13, 30, 4, 249981, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
