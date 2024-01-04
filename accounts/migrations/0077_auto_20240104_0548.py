# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0076_auto_20240104_0420'),
    ]

    operations = [
        migrations.AddField(
            model_name='authorityinfo',
            name='villages',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
