# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0005_domain_default_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='timezone',
            field=models.FloatField(default=7.0),
            preserve_default=True,
        ),
    ]
