 # -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards_func(apps, schema_editor):

    ReportType = apps.get_model("reports", "ReportType")
    ReportState = apps.get_model("reports", "ReportState")
    Report = apps.get_model("reports", "Report")

    for report_type in ReportType.objects.filter(id__gt=0, default_state__isnull=True):
        default_state = ReportState.objects.create(name='Report', code='report', report_type=report_type)
        ReportType.objects.filter(id=report_type.id).update(default_state=default_state)

        Report.objects.filter(type=report_type, state__isnull=True).update(state=default_state)



class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0040_auto_20150901_0351'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
