# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def initial_log_action(apps, schema_editor):
    LogAction = apps.get_model('logs', 'LogAction')
    action, created = LogAction.objects.get_or_create(
        name='USER_CREATE',
    )
    action.template = 'User `{{ log_item.object1.username }}` was created.'
    action.save()

    action, created = LogAction.objects.get_or_create(
        name='USER_EDIT',
    )
    action.template = 'User `{{ log_item.object1.username }}` field `{{ log_item.data.field }}` \
        was changed from {{ log_item.data.old }} to {{ log_item.data.new }}.'
    action.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0002_auto_20150128_0257'),
    ]

    operations = [
        migrations.RunPython(initial_log_action, backwards),
    ]
