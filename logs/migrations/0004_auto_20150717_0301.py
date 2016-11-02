# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def initial_log_action(apps, schema_editor):
    LogAction = apps.get_model('logs', 'LogAction')
    action, created = LogAction.objects.get_or_create(
        name='USER_LOGIN_CODE',
    )
    action.template = 'User `{{ log_item.object1.username }}` logged in system by code'
    action.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0003_auto_20150204_0659'),
    ]

    operations = [
        migrations.RunPython(initial_log_action, backwards),
    ]
