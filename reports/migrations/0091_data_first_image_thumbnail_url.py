# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_data_first_image_thumbnail_url(apps, schema_editor):

    Report = apps.get_model("reports", "Report")

    for report in Report.objects.filter(negative=True, test_flag=False, images__isnull=False):
        Report.objects.filter(id=report.id).update(first_image_thumbnail_url=report.images.all()[0].thumbnail_url)
        print 'update report.first_image_thumbnail_url %s' % report.id


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0090_auto_20170317_0513'),
    ]

    operations = [
        migrations.RunPython(migrate_data_first_image_thumbnail_url),
    ]
