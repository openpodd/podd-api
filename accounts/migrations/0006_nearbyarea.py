# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0014_auto_20141203_0354'),
        ('accounts', '0005_userdevice_gcm_reg_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='NearbyArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('area', models.OneToOneField(related_name='nearby', to='reports.AdministrationArea')),
                ('neighbors', models.ManyToManyField(related_name='neighbors', to='reports.AdministrationArea')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
