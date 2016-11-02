# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid1

from django.db import models, migrations


def fill_random_unique_data_to_report_type_code(apps, schema_editor):
    ReportType = apps.get_model('reports', 'ReportType')
    for report_type in ReportType.objects.all():
        report_type.code = str(uuid1())[0: 20]
        report_type.save()

def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0018_report_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='code',
            field=models.CharField(default=b'', max_length=100, blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(fill_random_unique_data_to_report_type_code, backwards),
    ]
