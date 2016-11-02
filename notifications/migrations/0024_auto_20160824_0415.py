# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0023_auto_20160622_0744'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notificationtemplate',
            options={'ordering': ['delta', 'id']},
        ),
        migrations.AddField(
            model_name='notificationtemplate',
            name='delta',
            field=models.IntegerField(default=0, max_length=5),
            preserve_default=True,
        ),
    ]
