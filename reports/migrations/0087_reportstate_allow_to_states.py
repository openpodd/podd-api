# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0086_auto_20160818_0317'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportstate',
            name='allow_to_states',
            field=models.ManyToManyField(related_name='allow_to_states_rel_+', null=True, to='reports.ReportState', blank=True),
            preserve_default=True,
        ),
    ]
