# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0006_notificationtemplate_authority'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='notificationauthority',
            unique_together=set([('template', 'authority')]),
        ),
    ]
