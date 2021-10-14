# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0071_auto_20191120_1156'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='lineId',
            new_name='line_id',
        ),
    ]
