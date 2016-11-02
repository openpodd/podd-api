# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flags', '0002_auto_20150112_0917'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flag',
            name='comment',
            field=models.OneToOneField(related_name='flags', to='reports.ReportComment'),
            preserve_default=True,
        ),
    ]
