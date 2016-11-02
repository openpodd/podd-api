# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0054_userdevice_is_deleted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authority',
            name='administration_areas',
        ),
        migrations.RemoveField(
            model_name='authority',
            name='report_types',
        ),
        migrations.RemoveField(
            model_name='authority',
            name='subscribes',
        ),
    ]
