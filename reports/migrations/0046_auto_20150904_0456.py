# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0045_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportStateUnique',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('report', models.ForeignKey(related_name='report_state_unique_report', to='reports.Report')),
                ('state', models.ForeignKey(related_name='report_state_unique_state', to='reports.ReportState')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='reportstateunique',
            unique_together=set([('report', 'state')]),
        ),
    ]
