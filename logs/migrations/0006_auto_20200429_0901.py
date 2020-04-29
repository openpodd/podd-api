# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def up_log_action(apps, schema_editor):
    LogAction = apps.get_model('logs', 'LogAction')
    action, created = LogAction.objects.get_or_create(
        name='REPORT_TO_CEP',
    )
    action.template = 'Report #{{ log_item.object_id1 }} was sent to cep with parameter {{ log_item.data }}'
    action.save()


def down_log_action(apps, schema_editor):
    LogAction = apps.get_model('logs', 'LogAction')
    action = LogAction.objects.get(
        name='REPORT_TO_CEP',
    )
    action.delete()



class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0005_auto_20160216_0943'),
    ]

    operations = [
        migrations.RunPython(up_log_action, down_log_action),
    ]
