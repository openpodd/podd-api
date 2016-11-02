# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0023_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='rendered_form_data',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='report',
            name='priority',
            field=models.PositiveIntegerField(default=0, choices=[(1, b'Ignore'), (2, b'OK'), (3, b'Contact'), (4, b'Follow'), (5, b'Case')]),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='CaseDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('epl', models.TextField()),
                ('code', models.CharField(unique=True, max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReportState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(unique=True, max_length=100)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='casedefinition',
            name='from_state',
            field=models.ForeignKey(related_name='from_state', to='reports.ReportState'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='casedefinition',
            name='report_type',
            field=models.ForeignKey(related_name='report_type', to='reports.ReportType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='casedefinition',
            name='to_state',
            field=models.ForeignKey(related_name='to_state', to='reports.ReportState'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reporttype',
            name='report_states',
            field=models.ManyToManyField(related_name='report_states', null=True, to='reports.ReportState', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='casedefinition',
            name='from_state',
            field=models.ForeignKey(related_name='from_state', blank=True, to='reports.ReportState', null=True),
            preserve_default=True,
        ),
    ]
