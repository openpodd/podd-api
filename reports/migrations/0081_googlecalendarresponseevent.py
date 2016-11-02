# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0005_domain_default_language'),
        ('reports', '0080_auto_20160205_0751'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleCalendarResponseEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event_id', models.TextField()),
                ('data', models.TextField()),
                ('deleted', models.BooleanField(default=False)),
                ('calendar', models.ForeignKey(related_name='calendar_events', to='reports.GoogleCalendarResponse')),
                ('domain', models.ForeignKey(related_name='domain_googlecalendarresponseevent', to='common.Domain')),
                ('report', models.ForeignKey(related_name='report_calendar_events', to='reports.Report')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
