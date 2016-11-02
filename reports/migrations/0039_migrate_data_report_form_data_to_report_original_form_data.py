 # -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db.models import F


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Report = apps.get_model("reports", "Report")
    Report.objects.filter(original_form_data='').update(original_form_data=F('form_data'))




class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0038_report_original_form_data'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
