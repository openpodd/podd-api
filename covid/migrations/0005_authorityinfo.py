# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0071_auto_20191120_1156'),
        ('covid', '0004_monitoringreport_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorityInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('line_notify_token', models.TextField(max_length=255, null=True, blank=True)),
                ('authority', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounts.Authority', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
