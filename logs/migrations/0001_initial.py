# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('template', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LogItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('object_id1', models.PositiveIntegerField()),
                ('object_id2', models.PositiveIntegerField(null=True)),
                ('serialized_data', models.TextField(blank=True)),
                ('action', models.ForeignKey(related_name='items', to='logs.LogAction')),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('object_type1', models.ForeignKey(related_name='log_items1', to='contenttypes.ContentType')),
                ('object_type2', models.ForeignKey(related_name='log_items2', blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ('-created_at',),
            },
            bases=(models.Model,),
        ),
    ]
