# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0057_administrationarea_mpoly'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='area_code',
            field=models.CharField(max_length=10, null=True),
            preserve_default=True,
        ),
    ]
