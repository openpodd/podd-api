# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0008_auto_20150824_0739'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notificationtemplate',
            name='reporter_feedback',
        ),
    ]
