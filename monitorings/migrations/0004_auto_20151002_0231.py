# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitorings', '0003_monitoring_domain'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monitoring',
            name='domain',
            field=models.ForeignKey(related_name='domain_monitoring', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
