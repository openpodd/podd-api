# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=100)),
                ('province_id', models.IntegerField()),
                ('level', models.IntegerField(default=0)),
                ('name_en', models.CharField(max_length=200)),
                ('name_th', models.CharField(max_length=200)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True)),
                ('address', models.TextField()),
                ('mpoly', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
                ('simplified_mpoly', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
                ('simplified_poly', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                ('simplified_type', models.CharField(max_length=50)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('parent', models.ForeignKey(related_name='children', to='areas.Area', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
