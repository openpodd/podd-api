# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_data_report_state(apps, schema_editor):

    Report = apps.get_model("reports", "Report")
    Flag = apps.get_model("flags", "Flag")


    for report in Report.objects.all():

        flag = None
        flags = Flag.objects.filter(comment__report=report)
        if flags.exists():
            flag = flags.latest('id')

        if flag:
            report.report_state = flag.state
            report.save()

class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0029_data_flags'),
        ('flags', '0005_data_flags'),
    ]

    operations = [
        #migrations.RunPython(migrate_data_report_state),
    ]
