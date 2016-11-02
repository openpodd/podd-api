# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('common', '0005_domain_default_language'),
        ('reports', '0072_administrationarea_qgis_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnimalLaboratoryCause',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('note', models.TextField(blank=True)),
                ('domain', models.ForeignKey(related_name='domain_animallaboratorycause', to='common.Domain')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReportInvestigation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.PositiveIntegerField(default=1, choices=[(1, b'Investigation: farm'), (2, b'Investigation: summary')])),
                ('form_data', models.TextField()),
                ('note', models.TextField(blank=True)),
                ('result', models.BooleanField(default=False)),
                ('file', models.URLField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(related_name='investigation_created_by', to=settings.AUTH_USER_MODEL)),
                ('domain', models.ForeignKey(related_name='domain_reportinvestigation', to='common.Domain')),
                ('parent', models.ForeignKey(blank=True, to='reports.ReportInvestigation', null=True)),
                ('report', models.ForeignKey(related_name='investigations', to='reports.Report')),
                ('updated_by', models.ForeignKey(related_name='investigation_updated_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReportLaboratoryResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(blank=True)),
                ('result', models.BooleanField(default=False)),
                ('file', models.URLField(null=True, blank=True)),
                ('farm_no', models.TextField()),
                ('sample_no', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cause', models.ForeignKey(related_name='laboratory_result_cause', to='reports.AnimalLaboratoryCause')),
                ('created_by', models.ForeignKey(related_name='laboratory_result_created_by', to=settings.AUTH_USER_MODEL)),
                ('domain', models.ForeignKey(related_name='domain_reportlaboratoryresult', to='common.Domain')),
                ('report', models.ForeignKey(related_name='laboratory_results', to='reports.Report')),
                ('updated_by', models.ForeignKey(related_name='laboratory_result_updated_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
