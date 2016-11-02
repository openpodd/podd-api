# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0021_reporttype_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='follow_days',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reporttype',
            name='followable',
            field=models.NullBooleanField(),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='report',
            name='test_flag',
            field=models.NullBooleanField(),
            preserve_default=True,
        ),
    ]
