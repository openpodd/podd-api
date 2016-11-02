 # -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def get_inherits_all(self):
    inherits = []
    _get_inherits_all(self, inherits)
    return inherits


def _get_inherits_all(self, inherits):
    for inherit in self.inherits.all():
        inherits.append(inherit)
        _get_inherits_all(inherit, inherits)

def forwards_func(apps, schema_editor):
    Authority = apps.get_model("accounts", "Authority")

    for authority in Authority.objects.all():
        for inherit in get_inherits_all(authority):
            inherit.subscribes.remove(authority)
            print '%s unsubscribe %s' % (inherit.name, authority.name)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0031_authority_group'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
