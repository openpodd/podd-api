# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import re
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0049_auto_20150917_0222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casedefinition',
            name='code',
            field=models.CharField(unique=True, max_length=255, validators=[django.core.validators.RegexValidator(re.compile(b'(?:^[A-Za-z][A-Za-z0-9]*)+'), 'Enter a valid code.', b'invalid')]),
            preserve_default=True,
        ),
    ]
