# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import re


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0024_auto_20150619_0421'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reportstate',
            options={'ordering': ['id']},
        ),
        migrations.RemoveField(
            model_name='reporttype',
            name='report_states',
        ),
        migrations.AddField(
            model_name='reportstate',
            name='report_type',
            field=models.ForeignKey(related_name='report_state_report_type', default=0, to='reports.ReportType'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='casedefinition',
            name='code',
            field=models.CharField(unique=True, max_length=255, validators=[django.core.validators.RegexValidator(re.compile(b'(?:[A-Z][a-z][0-9]*)+'), 'Enter a valid code.', b'invalid')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='casedefinition',
            name='report_type',
            field=models.ForeignKey(related_name='case_definition_report_type', to='reports.ReportType'),
            preserve_default=True,
        ),
    ]
