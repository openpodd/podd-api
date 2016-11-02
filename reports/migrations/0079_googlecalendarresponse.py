# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0055_auto_20160125_0705'),
        ('common', '0005_domain_default_language'),
        ('reports', '0078_reportlaboratoryfile_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleCalendarResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('calendar_id', models.CharField(max_length=255)),
                ('render_template', models.TextField(null=True, blank=True)),
                ('authorities', models.ManyToManyField(related_name='authority_calendar_response', null=True, to='accounts.Authority', blank=True)),
                ('domain', models.ForeignKey(related_name='domain_googlecalendarresponse', to='common.Domain')),
                ('report_states', models.ManyToManyField(related_name='reportstate_calendar_response', null=True, to='reports.ReportState', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
