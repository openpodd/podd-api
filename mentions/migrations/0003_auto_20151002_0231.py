# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mentions', '0002_mention_domain'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mention',
            name='domain',
            field=models.ForeignKey(related_name='domain_mention', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
