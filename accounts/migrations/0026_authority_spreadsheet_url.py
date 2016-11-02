# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0025_usercode'),
    ]

    operations = [
        migrations.AddField(
            model_name='authority',
            name='spreadsheet_url',
            field=models.URLField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='authority',
            name='inherits',
            field=models.ManyToManyField(related_name='authority_inherits', null=True, to='accounts.Authority', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='authority',
            name='subscribes',
            field=models.ManyToManyField(related_name='authority_subscribes', null=True, to='accounts.Authority', blank=True),
            preserve_default=True,
        ),
    ]
