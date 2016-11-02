# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0003_auto_20151002_0231'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='domain',
            name='domain',
        ),
    ]
