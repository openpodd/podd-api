# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0004_remove_domain_domain'),
        ('reports', '0059_auto_20151015_0025'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportTypeCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=512)),
                ('code', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('domain', models.ForeignKey(related_name='domain_reporttypecategory', to='common.Domain')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='reporttypecategory',
            unique_together=set([('domain', 'code')]),
        ),
        migrations.AddField(
            model_name='reporttype',
            name='categories',
            field=models.ManyToManyField(related_name='report_type_categories', null=True, to='reports.ReportTypeCategory', blank=True),
            preserve_default=True,
        ),
    ]
