# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0075_authority_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnimalRecord',
            fields=[
                ('id', models.CharField(max_length=64, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=400)),
                ('national_id', models.CharField(max_length=13)),
                ('phone', models.CharField(max_length=15)),
                ('addr_no', models.CharField(max_length=10)),
                ('addr_moo', models.CharField(max_length=10)),
                ('addr_subdistrict', models.CharField(max_length=100)),
                ('addr_district', models.CharField(max_length=100)),
                ('addr_soi', models.CharField(max_length=100)),
                ('addr_road', models.CharField(max_length=100)),
                ('animal_type', models.CharField(max_length=40)),
                ('animal_name', models.CharField(max_length=100)),
                ('animal_color', models.CharField(max_length=100)),
                ('animal_gender', models.CharField(max_length=10)),
                ('vaccine', models.CharField(max_length=10)),
                ('last_vaccine_date', models.DateField(null=True, blank=True)),
                ('spay', models.CharField(max_length=20)),
                ('spay_other', models.CharField(max_length=100, null=True, blank=True)),
                ('age_month', models.IntegerField()),
                ('age_year', models.IntegerField()),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('created_by', models.CharField(max_length=150)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_by', models.CharField(max_length=150)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_by', models.CharField(max_length=150, null=True, blank=True)),
                ('deleted_date', models.DateField(null=True, blank=True)),
                ('death_updated_date', models.DateField(null=True, blank=True)),
                ('death_updated_by', models.CharField(max_length=150, null=True, blank=True)),
                ('qr_code_url', models.CharField(max_length=300, null=True, blank=True)),
                ('authority', models.ForeignKey(to='accounts.Authority')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
