# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import re
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0093_auto_20170517_0351'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casedefinition',
            name='code',
            field=models.CharField(max_length=255, validators=[django.core.validators.RegexValidator(re.compile(b'(?:^[A-Za-z][A-Za-z0-9]*)+'), 'Enter a valid code.', b'invalid')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='code',
            field=models.CharField(max_length=100),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='casedefinition',
            unique_together=set([('domain', 'code')]),
        ),
        migrations.AlterUniqueTogether(
            name='reporttype',
            unique_together=set([('domain', 'code')]),
        ),
    ]
