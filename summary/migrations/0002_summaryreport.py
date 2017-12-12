# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0006_domain_timezone'),
        ('accounts', '0065_user_is_deleted'),
        ('summary', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SummaryReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('url', models.TextField()),
                ('authority', models.ForeignKey(to='accounts.Authority')),
                ('domain', models.ForeignKey(related_name='domain_summaryreport', verbose_name=b'Current domain', to='common.Domain')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
