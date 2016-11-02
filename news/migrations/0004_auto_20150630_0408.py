# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_auto_20150113_0807'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='type',
            field=models.CharField(max_length=100, choices=[(b'NEWS', b'News'), (b'UPDATED_REPORT_TYPE', b'Update report type'), (b'AREA', b'Area'), (b'SUBSCRIBE_AUTHORITY', b'Subscribe')]),
            preserve_default=True,
        ),
    ]
