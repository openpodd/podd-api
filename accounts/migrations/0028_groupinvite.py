# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        # ('auth', '0005_auto_20150211_0855'),
        ('accounts', '0027_auto_20150708_0645'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupInvite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(unique=True, max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('expired', models.DateTimeField()),
                ('groups', models.ManyToManyField(related_name='invite_groups', null=True, to='auth.Group', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
