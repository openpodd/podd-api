# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0028_auto_20191120_0950'),
    ]

    operations = [
        migrations.CreateModel(
            name='LineMessageGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('invite_number', models.CharField(unique=True, max_length=10)),
                ('remark', models.TextField(null=True, blank=True)),
                ('is_cancelled', models.BooleanField(default=False)),
                ('cancelled_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group_id', models.CharField(max_length=255, null=True, blank=True)),
                ('group_linked_at', models.DateTimeField(null=True, blank=True)),
                ('authority_id', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
