# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_auto_20150126_0826'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_volunteer',
            field=models.BooleanField(default=False, verbose_name='\u0e40\u0e1b\u0e47\u0e19\u0e2d\u0e32\u0e2a\u0e32\u0e2a\u0e21\u0e31\u0e04\u0e23\u0e42\u0e04\u0e23\u0e07\u0e01\u0e32\u0e23'),
            preserve_default=True,
        ),
    ]
