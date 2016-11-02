# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0053_auto_20151002_0231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='administrationarea',
            name='address',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='django_template',
            field=models.TextField(default=b'', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='form_definition',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='summary_template',
            field=models.TextField(default=b'', null=True, blank=True),
            preserve_default=True,
        ),
    ]
