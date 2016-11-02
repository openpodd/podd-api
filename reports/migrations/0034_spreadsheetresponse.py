# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0033_reporttype_authority'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpreadsheetResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=255)),
                ('administration_areas', models.ManyToManyField(related_name='administrationarea_response', null=True, to='reports.AdministrationArea', blank=True)),
                ('report_types', models.ManyToManyField(related_name='reporttype_response', null=True, to='reports.ReportType', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
