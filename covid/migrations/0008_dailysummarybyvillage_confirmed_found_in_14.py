# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0007_dailysummarybyvillage_confirmed'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysummarybyvillage',
            name='confirmed_found_in_14',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
