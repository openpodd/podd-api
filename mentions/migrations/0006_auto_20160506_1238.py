# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mentions', '0005_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mention',
            name='domain',
            field=models.ForeignKey(related_name='domain_mention', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
    ]
