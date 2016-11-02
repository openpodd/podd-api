# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_reportcomment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='report',
            old_name='negative_flag',
            new_name='negative',
        ),
        migrations.AddField(
            model_name='report',
            name='remark',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='administration_area',
            field=models.ForeignKey(related_name='reports', to='reports.AdministrationArea'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='date',
            field=models.DateTimeField(),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='report_location',
            field=django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='type',
            field=models.ForeignKey(related_name='reports', to='reports.ReportType'),
            preserve_default=True,
        ),
    ]
