 # -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    ReportType = apps.get_model("reports", "ReportType")
    ReportType.objects.filter(name=u'อื่นๆ').update(report_pre_save='report.negative = False')


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0042_reporttype_report_pre_save'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
