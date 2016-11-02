 # -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards_func(apps, schema_editor):

    UserDevice = apps.get_model("accounts", "UserDevice")

    for user_device in UserDevice.objects.all():
        user_device.domains.add(user_device.domain)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0042_userdevice_domains'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
