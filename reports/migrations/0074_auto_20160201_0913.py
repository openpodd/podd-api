# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0005_domain_default_language'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0073_animallaboratorycause_reportinvestigation_reportlaboratoryresult'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportLaboratoryCase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('case_no', models.TextField()),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(related_name='laboratory_result_created_by', to=settings.AUTH_USER_MODEL)),
                ('domain', models.ForeignKey(related_name='domain_reportlaboratorycase', to='common.Domain')),
                ('report', models.ForeignKey(related_name='laboratory_results', to='reports.Report')),
                ('updated_by', models.ForeignKey(related_name='laboratory_result_updated_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReportLaboratoryFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.URLField()),
                ('case', models.ForeignKey(related_name='laboratory_files', to='reports.ReportLaboratoryCase')),
                ('domain', models.ForeignKey(related_name='domain_reportlaboratoryfile', to='common.Domain')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReportLaboratoryItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sample_no', models.TextField()),
                ('note', models.TextField(blank=True)),
                ('case', models.ForeignKey(related_name='laboratory_items', to='reports.ReportLaboratoryCase')),
                ('domain', models.ForeignKey(related_name='domain_reportlaboratoryitem', to='common.Domain')),
                ('negative_causes', models.ManyToManyField(related_name='negative_causes', null=True, to='reports.AnimalLaboratoryCause', blank=True)),
                ('positive_causes', models.ManyToManyField(related_name='positive_causes', null=True, to='reports.AnimalLaboratoryCause', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='reportlaboratoryresult',
            name='cause',
        ),
        migrations.RemoveField(
            model_name='reportlaboratoryresult',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='reportlaboratoryresult',
            name='domain',
        ),
        migrations.RemoveField(
            model_name='reportlaboratoryresult',
            name='report',
        ),
        migrations.RemoveField(
            model_name='reportlaboratoryresult',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='ReportLaboratoryResult',
        ),
        migrations.RemoveField(
            model_name='reportinvestigation',
            name='form_data',
        ),
        migrations.RemoveField(
            model_name='reportinvestigation',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='reportinvestigation',
            name='type',
        ),
        migrations.AddField(
            model_name='reportinvestigation',
            name='investigation_date',
            field=models.DateField(default=datetime.datetime(2016, 2, 1, 9, 13, 53, 688762, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
