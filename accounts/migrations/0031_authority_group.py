# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0030_authority_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='authority',
            name='group',
            field=models.IntegerField(default=0, max_length=10),
            preserve_default=True,
        ),
    ]
