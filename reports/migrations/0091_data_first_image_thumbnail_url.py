# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings

from django.db import models, migrations
from common.constants import PARENT_TYPE_GENERAL



def migrate_data_first_image_thumbnail_url(apps, schema_editor):
    from haystack import connections as haystack_connections
    from reports.models import Report as ModelReport

    settings.CURRENT_DOMAIN_ID = 1

    Report = apps.get_model("reports", "Report")

    index = haystack_connections['default'].get_unified_index().get_index(ModelReport)

    for report in Report.objects.filter(parent__isnull=False):
        Report.objects.filter(id=report.id).update(parent_type=PARENT_TYPE_GENERAL)
        report = ModelReport.objects.get(id=report.id)
        index.update_object(report)
        print 'update report.parent_type %s' % report.id

    for report in Report.objects.filter(negative=True, test_flag=False, images__isnull=False):
        Report.objects.filter(id=report.id).update(first_image_thumbnail_url=report.images.all()[0].thumbnail_url)
        report = ModelReport.objects.get(id=report.id)
        index.update_object(report)
        print 'update report.first_image_thumbnail_url %s' % report.id


def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0090_auto_20170317_0513'),
    ]

    operations = [
        migrations.RunPython(migrate_data_first_image_thumbnail_url, noop),
    ]
