# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0039_migrate_data_report_form_data_to_report_original_form_data'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reportstate',
            options={'ordering': ['weight', 'id']},
        ),
        migrations.AddField(
            model_name='reportstate',
            name='weight',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reporttype',
            name='default_state',
            field=models.ForeignKey(related_name='report_type_default_state', blank=True, to='reports.ReportState', null=True),
            preserve_default=True,
        ),
    ]
