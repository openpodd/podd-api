# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitorings', '0004_auto_20151002_0231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monitoring',
            name='domain',
            field=models.ForeignKey(related_name='domain_monitoring', to='common.Domain'),
            preserve_default=True,
        ),
    ]
