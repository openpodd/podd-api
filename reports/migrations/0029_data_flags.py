# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_data_flags(apps, schema_editor):

    ReportType = apps.get_model("reports", "ReportType")
    ReportState = apps.get_model("reports", "ReportState")
    #Report = apps.get_model("reports", "Report")

    PRIORITY_CHOICES = (
        (1, 'Ignore'),
        (2, 'OK'),
        (3, 'Contact'),
        (4, 'Follow'),
        (5, 'Case'),
    )

    for report_type in ReportType.objects.all():
        for priority, name in PRIORITY_CHOICES:
            ReportState.objects.create(
                report_type=report_type,
                name=name,
                code=priority
            )

    #for report in Report.objects.all():
    #    report.




class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0028_report_state'),
    ]

    operations = [
        #migrations.RunPython(migrate_data_flags),
    ]
