# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0006_domain_timezone'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='is_active',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        #
        # migrations.RunSQL(
        #     "UPDATE commons_domain SET is_active = true where is_active is null"
        # )
    ]
