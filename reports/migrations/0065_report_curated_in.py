# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0064_remove_reporttype_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='curated_in',
            field=models.ManyToManyField(related_name='curated_reports', null=True, to='reports.AdministrationArea', blank=True),
            preserve_default=True,
        ),
    ]
