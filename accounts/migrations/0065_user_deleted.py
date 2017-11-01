# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0064_auto_20171005_0651'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='deleted',
            field=models.BooleanField(default=False, verbose_name='\u0e25\u0e1a\u0e41\u0e25\u0e49\u0e27'),
            preserve_default=True,
        ),
    ]
