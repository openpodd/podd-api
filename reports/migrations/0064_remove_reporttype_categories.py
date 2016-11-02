# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0063_reporttype_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reporttype',
            name='categories',
        ),
    ]
