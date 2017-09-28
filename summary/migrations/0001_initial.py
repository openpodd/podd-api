# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0006_domain_timezone'),
        ('accounts', '0063_authority_mpoly'),
    ]

    operations = [
        migrations.CreateModel(
            name='AggregateReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=500)),
                ('module', models.CharField(max_length=250)),
                ('filter_definition', models.TextField(default=b'', blank=True)),
                ('authorities', models.ManyToManyField(related_name='aggregate_report_authority', null=True, to='accounts.Authority', blank=True)),
                ('domain', models.ForeignKey(related_name='domain_aggregatereport', verbose_name=b'Current domain', to='common.Domain')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
