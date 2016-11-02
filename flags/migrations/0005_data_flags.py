# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_data_flags(apps, schema_editor):

    Flag = apps.get_model("flags", "Flag")
    ReportState = apps.get_model("reports", "ReportState")

    for flag in Flag.objects.all():

        print flag

        report_state = ReportState.objects.get(code=flag.priority, report_type=flag.comment.report.type)
        flag.state = report_state
        flag.save()


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0029_data_flags'),
        ('flags', '0004_flag_state'),
    ]

    operations = [
        #migrations.RunPython(migrate_data_flags),
    ]
