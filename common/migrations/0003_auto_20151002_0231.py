# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_domain_domain'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domain',
            name='domain',
            field=models.ForeignKey(related_name='domain_domain', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
