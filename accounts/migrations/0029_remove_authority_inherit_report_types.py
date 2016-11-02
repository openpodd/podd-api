# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0028_groupinvite'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authority',
            name='inherit_report_types',
        ),
    ]
