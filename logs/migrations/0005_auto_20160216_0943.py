# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def initial_log_action(apps, schema_editor):
    LogAction = apps.get_model('logs', 'LogAction')
    action, created = LogAction.objects.get_or_create(
        name='REPORT_STATE_CHANGE',
    )
    action.template = 'Report #{{ log_item.object_id1 }} state changed to `{{ log_item.object2.name }}`.'
    action.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0004_auto_20150717_0301'),
    ]

    operations = [
        migrations.RunPython(initial_log_action, backwards),
    ]
