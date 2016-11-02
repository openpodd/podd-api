# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0017_reporttype_django_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='parent',
            field=models.ForeignKey(related_name='children', blank=True, to='reports.Report', null=True),
            preserve_default=True,
        ),
    ]
