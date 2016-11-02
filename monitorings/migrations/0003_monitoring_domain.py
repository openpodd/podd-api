# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_domain_domain'),
        ('monitorings', '0002_auto_20141202_0903'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitoring',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
