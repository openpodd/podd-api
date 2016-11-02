# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0005_domain_default_language'),
        ('reports', '0072_administrationarea_qgis_id'),
        ('plans', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(max_length=200)),
                ('distance', models.IntegerField()),
                ('extra_data', models.TextField(null=True, blank=True)),
                ('domain', models.ForeignKey(related_name='domain_planlevel', to='common.Domain')),
                ('plan', models.ForeignKey(related_name='levels', to='plans.Plan')),
            ],
            options={
                'ordering': ['distance'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlanReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('log', models.TextField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('domain', models.ForeignKey(related_name='domain_planreport', to='common.Domain')),
                ('plan', models.ForeignKey(to='plans.Plan')),
                ('report', models.ForeignKey(to='reports.Report')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='plan',
            name='code',
            field=models.CharField(default='', unique=True, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='plan',
            name='name',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
