# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0105_auto_20220307_0342'),
        ('accounts', '0072_auto_20211014_0212'),
    ]

    operations = [
        migrations.AddField(
            model_name='authority',
            name='default_area',
            field=models.ForeignKey(related_name='default_for_authority', blank=True, to='reports.AdministrationArea', null=True),
            preserve_default=True,
        ),
    ]
