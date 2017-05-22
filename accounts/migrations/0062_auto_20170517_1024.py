# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0061_auto_20161104_0838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authority',
            name='code',
            field=models.CharField(max_length=255),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='authority',
            unique_together=set([('domain', 'code')]),
        ),
    ]
