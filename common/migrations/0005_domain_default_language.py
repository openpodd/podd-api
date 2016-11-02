# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0004_remove_domain_domain'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='default_language',
            field=models.CharField(default=b'en-us', max_length=20),
            preserve_default=True,
        ),
    ]
