# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0036_authority_admins'),
    ]

    operations = [
        migrations.AddField(
            model_name='authority',
            name='deep_subscribes',
            field=models.ManyToManyField(related_name='authority_deep_subscribes', null=True, to='accounts.Authority', blank=True),
            preserve_default=True,
        ),
    ]
