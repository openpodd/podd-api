# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_auto_20141110_0249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportcomment',
            name='report',
            field=models.ForeignKey(related_name='comments', to='reports.Report'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportimage',
            name='report',
            field=models.ForeignKey(related_name='images', to='reports.Report'),
            preserve_default=True,
        ),
    ]
