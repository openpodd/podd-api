# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def initial_custom_permission_data(apps, schema_editor):
    CustomPermission = apps.get_model('accounts', 'CustomPermission')
    CustomPermission.objects.get_or_create(
        name='View Dashboard Support', codename='view_dashboard_support')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_auto_20150216_0356'),
    ]

    operations = [
        migrations.RunPython(initial_custom_permission_data, backwards),
    ]
