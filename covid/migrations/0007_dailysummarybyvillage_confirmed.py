# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0006_auto_20211014_0643'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysummarybyvillage',
            name='confirmed',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
