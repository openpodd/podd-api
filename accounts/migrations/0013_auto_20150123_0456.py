# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_auto_20150119_0859'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupadministrationarea',
            name='role',
        ),
        migrations.RemoveField(
            model_name='groupreporttype',
            name='role',
        ),
    ]
