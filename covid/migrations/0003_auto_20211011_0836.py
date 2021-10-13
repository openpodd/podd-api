# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0002_auto_20211011_0759'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='dailysummary',
            unique_together=set([('authority', 'date')]),
        ),
    ]
