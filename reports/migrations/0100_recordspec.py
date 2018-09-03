# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0007_domain_is_active'),
        ('accounts', '0065_user_is_deleted'),
        ('reports', '0099_auto_20180502_0908'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecordSpec',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('tpl_header', models.TextField(null=True, blank=True)),
                ('tpl_subheader', models.TextField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('authority', models.ForeignKey(related_name='record_spec_authority', blank=True, to='accounts.Authority', null=True)),
                ('domain', models.ForeignKey(related_name='domain_recordspec', verbose_name=b'Current domain', to='common.Domain')),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='reports.RecordSpec', null=True)),
                ('type', models.ForeignKey(related_name='specs', to='reports.ReportType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
