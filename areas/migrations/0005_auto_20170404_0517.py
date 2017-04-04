# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0005_domain_default_language'),
        ('areas', '0004_auto_20151013_0941'),
    ]

    operations = [
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=1024)),
                ('level0_code', models.CharField(max_length=255)),
                ('level0_name', models.CharField(max_length=1024)),
                ('level1_code', models.CharField(max_length=255, null=True, blank=True)),
                ('level1_name', models.CharField(max_length=1024, null=True, blank=True)),
                ('level2_code', models.CharField(max_length=255, null=True, blank=True)),
                ('level2_name', models.CharField(max_length=1024, null=True, blank=True)),
                ('latitude', models.FloatField(null=True, blank=True)),
                ('longitude', models.FloatField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlaceCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=255)),
                ('level0_key', models.CharField(default=b'name', max_length=255, null=True, blank=True)),
                ('level0_label', models.CharField(default=b'Name', max_length=255, null=True, blank=True)),
                ('level1_key', models.CharField(max_length=255, null=True, blank=True)),
                ('level1_label', models.CharField(max_length=255, null=True, blank=True)),
                ('level2_key', models.CharField(max_length=255, null=True, blank=True)),
                ('level2_label', models.CharField(max_length=255, null=True, blank=True)),
                ('domain', models.ForeignKey(related_name='domain_placecategory', verbose_name=b'Current domain', to='common.Domain')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='place',
            name='category',
            field=models.ForeignKey(to='areas.PlaceCategory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='domain',
            field=models.ForeignKey(related_name='domain_place', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
    ]
