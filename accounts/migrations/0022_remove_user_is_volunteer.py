# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_auto_20150217_0755'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_volunteer',
        ),
    ]
