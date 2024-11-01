# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_domain_domain'),
        ('news', '0004_auto_20150630_0408'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
