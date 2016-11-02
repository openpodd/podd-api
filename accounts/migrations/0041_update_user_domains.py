 # -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards_func(apps, schema_editor):

    User = apps.get_model("accounts", "User")

    for user in User.objects.all():
        user.domains.add(user.domain)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0040_user_domains'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
