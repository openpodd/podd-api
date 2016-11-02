# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0053_merge'),
        ('news', '0009_auto_20151026_0909'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='authority',
            field=models.ForeignKey(blank=True, to='accounts.Authority', null=True),
            preserve_default=True,
        ),
    ]
