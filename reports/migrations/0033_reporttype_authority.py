# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0023_authority'),
        ('reports', '0032_auto_20150624_1007'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='authority',
            field=models.ForeignKey(related_name='report_type_authority', blank=True, to='accounts.Authority', null=True),
            preserve_default=True,
        ),
    ]
