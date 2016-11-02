# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0076_auto_20160203_0705'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportlaboratoryitem',
            name='sample_no',
            field=models.TextField(unique=True),
            preserve_default=True,
        ),
    ]
