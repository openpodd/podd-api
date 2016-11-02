# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_domain_domain'),
        ('mentions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mention',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
