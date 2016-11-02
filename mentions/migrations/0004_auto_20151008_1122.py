# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mentions', '0003_auto_20151002_0231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mention',
            name='domain',
            field=models.ForeignKey(related_name='domain_mention', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mention',
            name='seen_at',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
