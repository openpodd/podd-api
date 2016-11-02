# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0075_auto_20160202_0847'),
    ]

    operations = [
        migrations.AlterField(
            model_name='animallaboratorycause',
            name='name',
            field=models.TextField(unique=True),
            preserve_default=True,
        ),
    ]
