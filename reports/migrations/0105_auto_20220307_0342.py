# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0104_reporttype_merge_with_parent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='administrationarea',
            name='depth',
        ),
        migrations.RemoveField(
            model_name='administrationarea',
            name='lft',
        ),
        migrations.RemoveField(
            model_name='administrationarea',
            name='rgt',
        ),
        migrations.RemoveField(
            model_name='administrationarea',
            name='tree_id',
        ),
    ]
