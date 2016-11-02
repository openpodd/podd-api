# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0084_casedefinition_auto_create_report'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='casedefinition',
            options={'ordering': ['report_type', 'description']},
        ),
    ]
