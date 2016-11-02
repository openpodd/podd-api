# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def initial_log_action(apps, schema_editor):
    LogAction = apps.get_model('logs', 'LogAction')
    action, created = LogAction.objects.get_or_create(
        name='REPORT_CREATE',
    )
    action.template = 'Report #{{ log_item.object_id1 }} was created.'
    action.save()

    action, created = LogAction.objects.get_or_create(
        name='REPORT_FLAG_CHANGE',
    )
    action.template = 'Report #{{ log_item.object_id1 }} flag was changed to {{ log_item.object2.get_priority_display }}.'
    action.save()

    action, created = LogAction.objects.get_or_create(
        name='REPORT_SEND_MAIL_NEW_REPORT',
    )
    action.template = 'Report #{{ log_item.object_id1 }}\'s emails was sent to {{ log_item.data.emails }} after having new negative report.'
    action.save()

    action, created = LogAction.objects.get_or_create(
        name='REPORT_SEND_MAIL_NEW_CASE',
    )
    action.template = 'Report #{{ log_item.object_id1 }}\'s emails was sent to {{ log_item.data.emails }} after having new case.'
    action.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(initial_log_action, backwards),
    ]
