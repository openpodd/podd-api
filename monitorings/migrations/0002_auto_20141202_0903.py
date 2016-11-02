# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitorings', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='monitoring',
            old_name='file',
            new_name='uploadedfile',
        ),
    ]
