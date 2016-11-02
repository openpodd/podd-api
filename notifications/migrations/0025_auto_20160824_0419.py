# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0024_auto_20160824_0415'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notificationtemplate',
            options={'ordering': ['-delta', 'id']},
        ),
    ]
