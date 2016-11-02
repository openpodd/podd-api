# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0074_auto_20160201_0913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportlaboratorycase',
            name='case_no',
            field=models.TextField(unique=True),
            preserve_default=True,
        ),
    ]
