# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0012_auto_20141114_0820'),
        ('accounts', '0003_configuration_userdevice'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='administration_area',
            field=models.ForeignKey(related_name='users', blank=True, to='reports.AdministrationArea', null=True),
            preserve_default=True,
        ),
    ]
