# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('areas', '0005_auto_20170404_0517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='placecategory',
            name='level0_key',
            field=models.CharField(default=b'level0', max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='placecategory',
            name='level0_label',
            field=models.CharField(default=b'Level0', max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
