# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_domain_domain'),
        ('accounts', '0041_update_user_domains'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdevice',
            name='domains',
            field=models.ManyToManyField(default=1, related_name='+', to='common.Domain'),
            preserve_default=True,
        ),
    ]
