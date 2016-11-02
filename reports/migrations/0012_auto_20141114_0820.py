# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_default_positive_report_type(apps, schema_editor):
    ReportType = apps.get_model('reports', 'ReportType')
    try:
        ReportType.objects.get(id = 0)
    except ReportType.DoesNotExist:
        ReportType.objects.create(
            id = 0,
            name = 'Positive Report Type',
            form_definition = {},
            version = 0,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0011_reporttype_template'),
    ]

    operations = [
        migrations.RunPython(create_default_positive_report_type),
    ]
